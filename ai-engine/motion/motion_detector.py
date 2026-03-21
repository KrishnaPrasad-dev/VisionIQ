import cv2
import numpy as np

class MotionDetector:

    def __init__(self, threshold=5000):
        """
        threshold = number of changed pixels required to consider motion
        """
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=50,
            detectShadows=False
        )

        self.threshold = threshold

    def detect(self, frame, return_mask=False):
        """Return frame-level motion metrics and optional foreground mask."""

        fg_mask = self.bg_subtractor.apply(frame)

        # Remove noise
        fg_mask = cv2.GaussianBlur(fg_mask, (5, 5), 0)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        # Count changed pixels
        motion_pixels = cv2.countNonZero(fg_mask)
        frame_area = float(frame.shape[0] * frame.shape[1])
        motion_ratio = motion_pixels / frame_area if frame_area > 0 else 0.0
        detected = motion_pixels > self.threshold

        result = {
            "detected": bool(detected),
            "motion_pixels": int(motion_pixels),
            "motion_ratio": float(motion_ratio),
        }

        if return_mask:
            result["mask"] = fg_mask

        return result

    def motion_in_bbox(self, mask, bbox):
        """Estimate motion ratio inside a bounding box."""
        x1, y1, x2, y2 = bbox
        h, w = mask.shape[:2]
        x1 = max(0, min(w - 1, int(x1)))
        x2 = max(0, min(w, int(x2)))
        y1 = max(0, min(h - 1, int(y1)))
        y2 = max(0, min(h, int(y2)))

        if x2 <= x1 or y2 <= y1:
            return 0.0

        region = mask[y1:y2, x1:x2]
        area = float((x2 - x1) * (y2 - y1))
        if area <= 0:
            return 0.0
        return float(cv2.countNonZero(region) / area)