import numpy as np
import cv2

from detection.detector import detector
from motion.motion_detector import MotionDetector
from tracking.tracker import dwell_tracker

from scoring.threat_score import calculate_threat_score
from scoring.score_smoother import apply_score_decay
from scoring.status_manager import get_status

from visualization.annotator import annotate_frame
import config.config as config


# create motion detector instance
motion_detector = MotionDetector()


def process_frame(frame):

    # ── DETECTION ─────────────────────────────────────
    detections = detector.detect(frame)

    # ── MOTION ANALYSIS ───────────────────────────────
    motion_detected = motion_detector.detect(frame)

    # convert to structure expected by scorer/annotator
    motion_data = {
        "running": False,
        "panic": False,
        "abandoned": False,
        "motion_score": 10 if motion_detected else 0,
        "flow_vectors": []
    }

    # ── ZONE CHECK ────────────────────────────────────
    zone_results = []
    loitering_ids = []

    if len(detections) > 0:

        for zone in config.zones:

            zone_name = zone["name"]
            threat_level = zone["threat_level"]
            coords = np.array(zone["coords"], np.int32)

            triggered = False
            in_zone_flags = []

            for i in range(len(detections)):

                x1, y1, x2, y2 = detections.xyxy[i]

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                inside = cv2.pointPolygonTest(coords, (cx, cy), False) >= 0
                in_zone_flags.append(inside)

                if inside:
                    triggered = True

            zone_results.append((zone_name, triggered, threat_level))

            # ── LOITERING CHECK ─────────────────────
            if detections.tracker_id is not None:

                track_ids = detections.tracker_id

                alerts = dwell_tracker.update(
                    track_ids,
                    zone_name,
                    in_zone_flags
                )

                for track_id, zone, dwell in alerts:
                    loitering_ids.append(track_id)

    # ── THREAT SCORE ──────────────────────────────────
    score = calculate_threat_score(
    person_count=len(detections),
    zone_results=zone_results,
    loitering_count=len(loitering_ids),
    motion=motion_data
)

    # smooth score
    score = apply_score_decay(score)

    # determine status
    status = get_status(score)

    # ── ANNOTATE FRAME ────────────────────────────────
    annotated = annotate_frame(
        frame,
        detections,
        zone_results,
        score,
        status,
        loitering_ids,
        motion_data
    )

    return annotated, score, status