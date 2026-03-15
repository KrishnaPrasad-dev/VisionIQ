import torch
from ultralytics import YOLO
import supervision as sv
import numpy as np


class PersonDetector:

    def __init__(self):

        print("Loading YOLO model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = YOLO("models/yolov8n.pt")

        self.model.to(self.device)

        # warmup run (improves first inference speed)
        dummy = np.zeros((480, 640, 3), dtype=np.uint8)
        self.model(dummy, classes=[0], conf=0.5, verbose=False)

        print(f"YOLO ready on {self.device}")

    def detect(self, frame):

        results = self.model(
            frame,
            classes=[0],
            conf=0.5,
            imgsz=640,
            device=self.device,
            verbose=False
        )

        return sv.Detections.from_ultralytics(results[0])


# IMPORTANT: create global instance
detector = PersonDetector()