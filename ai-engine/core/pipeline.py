import cv2

from detection.detector import detector
from core.threat import calculate_threat_score, get_status


def process_frame(frame, camera_config):

    # -------------------------------
    # DETECTION
    # -------------------------------
    detections = detector.detect(frame)
    persons = [d for d in detections if d["class"] == "person"]

    # -------------------------------
    # ZONES
    # -------------------------------
    zone_hits = []

    for person in persons:
        x1, y1, x2, y2 = person["bbox"]

        cx = int((x1 + x2) / 2)
        cy = int(y2)

        for zone in camera_config.get("zones", []):
            polygon = zone["coordinates"]

            inside = cv2.pointPolygonTest(polygon, (cx, cy), False)

            if inside >= 0:
                zone_hits.append({
                    "zone": zone["name"],
                    "threat": zone.get("threat_level", 1)
                })

    # -------------------------------
    # METRICS
    # -------------------------------
    people_count = len(persons)
    loiter_alerts = []

    # -------------------------------
    # THREAT SCORE
    # -------------------------------
    score = calculate_threat_score(
        people_count=people_count,
        zone_hits=zone_hits,
        loitering=loiter_alerts,
        rules=camera_config["rules"]
    )

    status = get_status(score)

    return {
        "frame": frame,
        "detections": persons,
        "people_count": people_count,
        "zone_hits": zone_hits,
        "loitering": loiter_alerts,
        "score": score,
        "status": status
    }


# -------------------------------
# DRAW OVERLAY
# -------------------------------
def draw_overlay(frame, result, events):

    # BOXES
    for det in result["detections"]:
        x1, y1, x2, y2 = det["bbox"]
        conf = det["confidence"]

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(frame, f"{conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2)

    # PEOPLE COUNT
    cv2.putText(frame,
                f"People: {result['people_count']}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2)

    # STATUS
    status = result["status"]

    color = (0, 255, 0)
    if status == "WARNING":
        color = (0, 255, 255)
    elif status == "DANGER":
        color = (0, 0, 255)

    cv2.putText(frame,
                f"Status: {status}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                3)

    # SCORE
    cv2.putText(frame,
                f"Score: {result['score']}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2)

    # ALERTS
    y = 160
    for event in events:
        cv2.putText(frame,
                    f"ALERT: {event['type']}",
                    (20, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2)
        y += 30

    return frame