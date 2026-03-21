import torch
from ultralytics import YOLO
import numpy as np


class PersonDetector:

    def __init__(self, use_fp16=True, optimize=True):
        print("Loading YOLO model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Using device: {self.device}")

        self.model = YOLO("models/yolov8n.pt")
        self.model.to(self.device)
        self.imgsz = 512 if self.device == "cpu" else 640
        
        # Optimization: Fuse model layers for faster inference
        if optimize:
            try:
                self.model.fuse()
                print("Model fused for faster inference")
            except:
                pass
        
        # Use FP16 (half precision) for faster inference if available
        self.use_fp16 = use_fp16 and self.device == "cuda"

        # Warmup
        dummy = np.zeros((480, 640, 3), dtype=np.uint8)
        self.model(dummy, classes=[0], conf=0.5, verbose=False)

        print(f"YOLO ready on {self.device}")
        self.frame_count = 0
        self.target_classes = [0, 67]  # person, dining table

    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union between two boxes"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        inter_area = max(0, inter_xmax - inter_xmin) * max(0, inter_ymax - inter_ymin)
        
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0

    def _apply_nms(self, detections, iou_threshold=0.5):
        """Apply Non-Maximum Suppression to remove overlapping detections"""
        if not detections:
            return detections
        
        # Sort by confidence descending
        sorted_dets = sorted(detections, key=lambda x: x["confidence"], reverse=True)
        
        keep = []
        for det in sorted_dets:
            remove = False
            for kept in keep:
                iou = self._calculate_iou(det["bbox"], kept["bbox"])
                if iou > iou_threshold:
                    remove = True
                    break
            if not remove:
                keep.append(det)
        
        return keep

    def detect(self, frame):
        """
        Detect people in frame
        
        Args:
            frame: Input image
            frame: Input image
        
        Returns:
            List of detections
        """
        self.frame_count += 1
        
        results = self.model(
            frame, 
            classes=self.target_classes,
            conf=0.35,
            iou=0.45,
            imgsz=self.imgsz,
            max_det=80,
            verbose=False,
            half=self.use_fp16,
        )

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

                # Filter out low confidence and very small boxes
                box_area = (x2 - x1) * (y2 - y1)
                if label == "person":
                    if conf < 0.30 or box_area < 650:
                        continue
                elif label in ("dining table", "table"):
                    if conf < 0.22 or box_area < 2200:
                        continue
                else:
                    continue

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class": label,
                    "confidence": conf,
                    "area": box_area
                })

        # Apply NMS to remove overlapping detections
        detections = self._apply_nms(detections, iou_threshold=0.4)

        return detections


detector = PersonDetector(use_fp16=True, optimize=True)