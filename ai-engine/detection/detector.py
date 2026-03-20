import torch
from ultralytics import YOLO
import numpy as np


class PersonDetector:

    def __init__(self):
        print("Loading YOLO model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = YOLO("models/yolov8n.pt")
        self.model.to(self.device)

        # warmup
        dummy = np.zeros((480, 640, 3), dtype=np.uint8)
        self.model(dummy, classes=[0], conf=0.5, verbose=False)

        print(f"YOLO ready on {self.device}")

    def detect(self, frame):
        results = self.model(frame, classes=[0], conf=0.4, verbose=False)

        detections = []

        for r in results:
            boxes = r.boxes

            if boxes is None:
                continue

            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                label = self.model.names[cls_id]

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class": label,
                    "confidence": conf
                })

        return detections


detector = PersonDetector()