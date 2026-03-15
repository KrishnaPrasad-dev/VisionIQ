from config.config import CONFIDENCE_THRESHOLD, TARGET_CLASSES
from detection.model_loader import load_model

model = load_model()

def detect(frame):

    results = model(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        classes=TARGET_CLASSES,
        verbose=False
    )

    detections = []

    for r in results:
        for box in r.boxes:

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])

            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": confidence
            })

    return detections