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

    def detect(self, frame):
        """
        Returns True if motion is detected
        """

        fg_mask = self.bg_subtractor.apply(frame)

        # Remove noise
        fg_mask = cv2.GaussianBlur(fg_mask, (5,5), 0)

        # Count changed pixels
        motion_pixels = cv2.countNonZero(fg_mask)

        if motion_pixels > self.threshold:
            return True

        return False