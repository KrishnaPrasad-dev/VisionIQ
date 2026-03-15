import cv2
import numpy as np
import config.config as config


def annotate_frame(
    frame,
    detections,
    zone_results,
    score,
    status,
    loitering_ids,
    motion
):

    annotated = frame.copy()

    # ───────── DRAW ZONES ─────────
    for zone in config.zones:

        coords = np.array(zone["coords"], np.int32)

        cv2.polylines(
            annotated,
            [coords],
            isClosed=True,
            color=(0, 200, 255),
            thickness=2
        )

        cv2.putText(
            annotated,
            zone["name"],
            tuple(coords[0]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,200,255),
            2
        )

    # ───────── DRAW DETECTIONS ─────────
    for i in range(len(detections)):

        x1, y1, x2, y2 = detections.xyxy[i]

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        color = (0,255,0)

        cv2.rectangle(
            annotated,
            (x1,y1),
            (x2,y2),
            color,
            2
        )

        label = "Person"

        if detections.tracker_id is not None:

            track_id = int(detections.tracker_id[i])

            label = f"ID {track_id}"

            if track_id in loitering_ids:
                label += " LOITER"

        cv2.putText(
            annotated,
            label,
            (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    # ───────── HUD BAR ─────────
    hud_color = (0,255,0)

    if status == "SUSPICIOUS":
        hud_color = (0,200,255)

    if status == "CRITICAL":
        hud_color = (0,0,255)

    cv2.rectangle(
        annotated,
        (0,0),
        (annotated.shape[1],50),
        (20,20,20),
        -1
    )

    cv2.putText(
        annotated,
        f"THREAT: {int(score)} | {status}",
        (10,32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        hud_color,
        2
    )

    cv2.putText(
        annotated,
        f"People: {len(detections)} | Mode: {config.mode}",
        (350,32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2
    )

    # ───────── MOTION LABELS ─────────
    motion_text = []

    if motion.get("running"):
        motion_text.append("RUNNING")

    if motion.get("panic"):
        motion_text.append("PANIC")

    if motion.get("abandoned"):
        motion_text.append("ABANDONED")

    if len(loitering_ids) > 0:
        motion_text.append(f"LOITERING:{len(loitering_ids)}")

    if motion_text:

        cv2.putText(
            annotated,
            " | ".join(motion_text),
            (10, annotated.shape[0] - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,0,255),
            2
        )

    return annotated