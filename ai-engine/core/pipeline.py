import cv2
import numpy as np
import os
from datetime import datetime

from detection.detector import detector
from core.threat import calculate_threat_score, get_status
from core.normal_behavior import normal_behavior_model
from motion.motion_detector import MotionDetector


class FrameHistory:
    """Simple centroid tracker for loitering and running behavior."""

    def __init__(
        self,
        fps=15,
        max_history=30,
        match_distance=90,
        max_missed=8,
        loiter_seconds=3,
        loiter_speed=2.0,
        running_speed=13.0,
    ):
        self.fps = max(1, int(fps))
        self.max_history = max_history
        self.match_distance = match_distance
        self.max_missed = max_missed
        self.loiter_frames = int(loiter_seconds * self.fps)
        self.loiter_speed = loiter_speed
        self.running_speed = running_speed
        self.next_id = 0
        self.tracks = {}

    def _distance(self, p1, p2):
        return float(np.hypot(p1[0] - p2[0], p1[1] - p2[1]))

    def _new_track(self, center):
        self.tracks[self.next_id] = {
            "positions": [center],
            "velocity": 0.0,
            "missed": 0,
            "dwell_frames": 0,
            "seen_frames": 1,
        }
        self.next_id += 1

    def update(self, detections):
        centers = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            centers.append((int((x1 + x2) / 2), int((y1 + y2) / 2)))

        assigned_tracks = set()
        assigned_dets = set()

        if self.tracks and centers:
            candidates = []
            for tid, track in self.tracks.items():
                last = track["positions"][-1]
                for di, c in enumerate(centers):
                    dist = self._distance(last, c)
                    if dist <= self.match_distance:
                        candidates.append((dist, tid, di))

            candidates.sort(key=lambda x: x[0])
            for dist, tid, di in candidates:
                if tid in assigned_tracks or di in assigned_dets:
                    continue
                track = self.tracks[tid]
                prev = track["positions"][-1]
                track["positions"].append(centers[di])
                if len(track["positions"]) > self.max_history:
                    track["positions"].pop(0)

                inst_speed = self._distance(prev, centers[di])
                track["velocity"] = 0.65 * track["velocity"] + 0.35 * inst_speed
                track["seen_frames"] += 1
                track["missed"] = 0

                if track["velocity"] <= self.loiter_speed:
                    track["dwell_frames"] += 1
                else:
                    track["dwell_frames"] = 0

                assigned_tracks.add(tid)
                assigned_dets.add(di)

        for di, c in enumerate(centers):
            if di not in assigned_dets:
                self._new_track(c)

        to_delete = []
        for tid, track in self.tracks.items():
            if tid not in assigned_tracks and track["positions"]:
                track["missed"] += 1
                if track["missed"] > self.max_missed:
                    to_delete.append(tid)
        for tid in to_delete:
            del self.tracks[tid]

        loitering_ids = []
        running_ids = []
        velocities = []
        confirmed_tracks = 0
        for tid, track in self.tracks.items():
            velocities.append(track["velocity"])
            if track["seen_frames"] >= 3 and track["missed"] == 0:
                confirmed_tracks += 1
            if track["seen_frames"] >= 8 and track["dwell_frames"] >= self.loiter_frames:
                loitering_ids.append(tid)
            if track["seen_frames"] >= 5 and track["velocity"] >= self.running_speed:
                running_ids.append(tid)

        avg_velocity = float(np.mean(velocities)) if velocities else 0.0
        return confirmed_tracks, loitering_ids, running_ids, avg_velocity

    def get_track_stability(self):
        """Return confidence score based on track consistency"""
        if not self.tracks:
            return 0

        avg_track_length = np.mean([len(track["positions"]) for track in self.tracks.values()])
        return float(min(avg_track_length / 20.0, 1.0))


class AssetDamageDetector:
    """Detect likely table breakage/tampering from table disappearance + motion."""

    def __init__(self):
        self.baseline_area = None
        self.missing_frames = 0
        self.last_table_boxes = []

    def _iou(self, a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
        area_b = max(1, (bx2 - bx1) * (by2 - by1))
        return inter / float(area_a + area_b - inter)

    def update(self, tables, persons, motion_info, running_count, motion_detector_ref):
        table_area = sum(t["area"] for t in tables)
        motion_ratio = motion_info.get("motion_ratio", 0.0)
        mask = motion_info.get("mask")

        if tables:
            self.missing_frames = 0
            if self.baseline_area is None:
                self.baseline_area = float(table_area)
            else:
                self.baseline_area = 0.92 * self.baseline_area + 0.08 * float(table_area)
            self.last_table_boxes = [t["bbox"] for t in tables]
        else:
            if self.baseline_area is not None:
                self.missing_frames += 1

        if self.baseline_area is None:
            return False, 0.0

        drop_ratio = 1.0
        if self.baseline_area > 0:
            drop_ratio = max(0.0, min(1.0, table_area / self.baseline_area))

        # Person near table region
        person_near_table = False
        for p in persons:
            pb = p["bbox"]
            for tb in self.last_table_boxes:
                if self._iou(pb, tb) > 0.02:
                    person_near_table = True
                    break
            if person_near_table:
                break

        local_motion = 0.0
        if mask is not None and self.last_table_boxes:
            local_vals = [motion_detector_ref.motion_in_bbox(mask, b) for b in self.last_table_boxes]
            if local_vals:
                local_motion = float(np.mean(local_vals))

        area_drop = drop_ratio < 0.55
        sustained_missing = self.missing_frames >= 8
        violent_motion = motion_ratio > 0.035 or local_motion > 0.06
        aggressive_context = running_count > 0 or person_near_table

        suspected = (area_drop or sustained_missing) and violent_motion and aggressive_context
        confidence = 0.0
        if suspected:
            confidence = min(1.0, (1 - drop_ratio) * 0.55 + local_motion * 2.2 + motion_ratio * 0.7)
        return suspected, confidence


# Global frame history tracker
frame_history = FrameHistory(
    fps=15,
    loiter_seconds=float(os.getenv("QUANTUMEYE_LOITER_SECONDS", "12")),
    loiter_speed=float(os.getenv("QUANTUMEYE_LOITER_SPEED", "1.5")),
)
motion_detector = MotionDetector(threshold=4500)
asset_damage_detector = AssetDamageDetector()

LOITER_MIN_COUNT = int(os.getenv("QUANTUMEYE_LOITER_MIN_COUNT", "2"))


def process_frame(frame, camera_config):

    # -------------------------------
    # DETECTION
    # -------------------------------
    detections = detector.detect(frame)
    persons = [d for d in detections if d["class"] == "person"]
    tables = [d for d in detections if d["class"] in ("dining table", "table")]

    motion_info = motion_detector.detect(frame, return_mask=True)

    # -------------------------------
    # TEMPORAL TRACKING & LOITERING
    # -------------------------------
    stable_person_count, loitering_ids, running_ids, avg_velocity = frame_history.update(persons)
    table_breakage, breakage_confidence = asset_damage_detector.update(
        tables=tables,
        persons=persons,
        motion_info=motion_info,
        running_count=len(running_ids),
        motion_detector_ref=motion_detector,
    )

    # -------------------------------
    # ZONES
    # -------------------------------
    zone_hits = []

    for person in persons:
        x1, y1, x2, y2 = person["bbox"]

        cx = int((x1 + x2) / 2)
        cy = int(y2)

        for zone in camera_config.get("zones", []):
            polygon = np.array(zone.get("coordinates", []), dtype=np.int32)
            if polygon.size == 0:
                continue

            inside = cv2.pointPolygonTest(polygon, (float(cx), float(cy)), False)

            if inside >= 0:
                zone_hits.append({
                    "zone": zone["name"],
                    "threat": zone.get("threat_level", "low")
                })

    # -------------------------------
    # METRICS
    # -------------------------------
    raw_people_count = len(persons)
    # Prefer confirmed temporal tracks for scoring accuracy, but keep minimum responsiveness.
    people_count = max(stable_person_count, min(raw_people_count, 1))
    # Require at least 2 independent loitering tracks to reduce false positives in normal shop scenes.
    loiter_alerts = len(loitering_ids) >= LOITER_MIN_COUNT
    now = datetime.now()

    metrics = {
        "people_count": people_count,
        "raw_people_count": raw_people_count,
        "motion_ratio": motion_info.get("motion_ratio", 0.0),
        "avg_velocity": avg_velocity,
        "running_count": len(running_ids),
        "loitering_count": len(loitering_ids),
        "hour": now.hour,
        "weekday": now.weekday(),
    }

    camera_id = camera_config.get("camera_id", "default")

    baseline = normal_behavior_model.score(camera_id=camera_id, metrics=metrics, ts=now)
    anomaly_score = baseline["anomaly_score"]
    baseline_ready = baseline["baseline_ready"]
    baseline_samples = baseline["baseline_samples"]

    # Learn from low-risk frames only to avoid training on attacks/anomalies.
    rules = camera_config.get("rules", {})
    max_people = int(rules.get("maxPeople", 5))
    low_risk_frame = (
        people_count <= max_people
        and len(zone_hits) == 0
        and len(running_ids) == 0
        and not loiter_alerts
        and not table_breakage
        and motion_info.get("motion_ratio", 0.0) < 0.08
    )
    if rules.get("adaptiveLearning", True):
        normal_behavior_model.update(
            camera_id=camera_id,
            metrics=metrics,
            ts=now,
            allow_learning=low_risk_frame,
        )

    # -------------------------------
    # THREAT SCORE
    # -------------------------------
    score = calculate_threat_score(
        people_count=people_count,
        zone_hits=zone_hits,
        loitering=loiter_alerts,
        rules=camera_config["rules"],
        loitering_count=len(loitering_ids),
        running_count=len(running_ids),
        vandalism=table_breakage,
        vandalism_confidence=breakage_confidence,
        anomaly_score=anomaly_score,
        baseline_ready=baseline_ready,
        track_stability=frame_history.get_track_stability(),
        avg_velocity=avg_velocity,
    )

    status = get_status(score)

    return {
        "frame": frame,
        "detections": persons,
        "people_count": people_count,
        "raw_people_count": raw_people_count,
        "stable_person_count": stable_person_count,
        "zone_hits": zone_hits,
        "tables_count": len(tables),
        "loitering": loiter_alerts,
        "loitering_ids": loitering_ids,
        "running": len(running_ids) > 0,
        "running_ids": running_ids,
        "table_breakage": table_breakage,
        "table_breakage_confidence": breakage_confidence,
        "motion_ratio": motion_info.get("motion_ratio", 0.0),
        "anomaly_score": anomaly_score,
        "baseline_ready": baseline_ready,
        "baseline_samples": baseline_samples,
        "learning_frame_used": low_risk_frame,
        "avg_velocity": avg_velocity,
        "score": score,
        "status": status,
        "track_stability": frame_history.get_track_stability()
    }


# -------------------------------
# DRAW OVERLAY
# -------------------------------
def draw_overlay(frame, result, events):

    # BOXES
    for det in result["detections"]:
        x1, y1, x2, y2 = det["bbox"]
        conf = det["confidence"]

        color = (0, 255, 0)  # Green for safe
        if result["status"] == "WARNING":
            color = (0, 255, 255)  # Yellow
        elif result["status"] == "DANGER":
            color = (0, 0, 255)  # Red
        elif result["status"] == "CRITICAL":
            color = (0, 0, 180)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(frame, f"P:{conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2)

    # PEOPLE COUNT
    cv2.putText(frame,
                f"People: {result['people_count']}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2)

    # LOITERING ALERT
    if result["loitering"]:
        cv2.putText(frame,
                    f"LOITERING DETECTED ({len(result['loitering_ids'])})",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2)

    if result.get("running"):
        cv2.putText(frame,
                    f"RUNNING DETECTED ({len(result.get('running_ids', []))})",
                    (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2)

    if result.get("table_breakage"):
        cv2.putText(frame,
                    f"TABLE DAMAGE SUSPECTED ({result.get('table_breakage_confidence', 0):.2f})",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2)

    # STATUS
    status = result["status"]

    color = (0, 255, 0)
    if status == "WARNING":
        color = (0, 255, 255)
    elif status == "DANGER":
        color = (0, 0, 255)
    elif status == "CRITICAL":
        color = (0, 0, 180)

    cv2.putText(frame,
                f"Status: {status}",
                (20, 175),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                3)

    # SCORE
    cv2.putText(frame,
                f"Score: {result['score']}",
                (20, 215),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2)

    learn_tag = "READY" if result.get("baseline_ready") else "LEARNING"
    cv2.putText(frame,
                f"Anomaly: {result.get('anomaly_score', 0.0):.2f} | Baseline: {learn_tag}",
                (20, 245),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2)

    # ALERTS
    y = 275
    for event in events:
        cv2.putText(frame,
                    f"ALERT: {event['type']} ({event.get('severity', 'info')})",
                    (20, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2)
        y += 30

    return frame