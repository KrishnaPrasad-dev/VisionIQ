import torch
from ultralytics import YOLO
import numpy as np
import os


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
        self.person_min_conf = float(os.getenv("QUANTUMEYE_PERSON_MIN_CONF", "0.32"))
        self.person_min_area_px = int(os.getenv("QUANTUMEYE_PERSON_MIN_AREA", "650"))
        self.person_min_area_ratio = float(os.getenv("QUANTUMEYE_PERSON_MIN_AREA_RATIO", "0.0006"))
        self.table_min_conf = float(os.getenv("QUANTUMEYE_TABLE_MIN_CONF", "0.24"))
        self.table_min_area_px = int(os.getenv("QUANTUMEYE_TABLE_MIN_AREA", "2200"))

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

        # Run NMS per class so overlapping person/table boxes do not suppress each other.
        by_class = {}
        for det in detections:
            by_class.setdefault(det["class"], []).append(det)

        kept_all = []
        for _, class_dets in by_class.items():
            kept_all.extend(self._nms_single_class(class_dets, iou_threshold=iou_threshold))
        return kept_all

    def _nms_single_class(self, detections, iou_threshold=0.5):
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
        frame_h, frame_w = frame.shape[:2]
        frame_area = max(1, frame_h * frame_w)
        adaptive_person_min_area = max(
            self.person_min_area_px,
            int(frame_area * self.person_min_area_ratio),
        )
        
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
                    bw = max(1, x2 - x1)
                    bh = max(1, y2 - y1)
                    aspect_ratio = bw / float(bh)
                    # Person boxes are typically taller than wide; filter implausible shapes.
                    if aspect_ratio < 0.18 or aspect_ratio > 1.2:
                        continue

                    min_conf = self.person_min_conf + 0.08 if box_area < adaptive_person_min_area * 2 else self.person_min_conf
                    if conf < min_conf or box_area < adaptive_person_min_area:
                        continue
                elif label in ("dining table", "table"):
                    if conf < self.table_min_conf or box_area < self.table_min_area_px:
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