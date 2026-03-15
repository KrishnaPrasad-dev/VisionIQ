from detection.detector import detect
from utils.image_utils import resize_frame
from motion.motion_detector import MotionDetector
from config.config import DETECTION_INTERVAL

motion_detector = MotionDetector()

frame_count = 0

def process_frame(frame):

    global frame_count
    frame_count += 1

    frame = resize_frame(frame)

    detections = []

    motion = motion_detector.detect(frame)

    if motion and frame_count % DETECTION_INTERVAL == 0:
        detections = detect(frame)

    return frame, detections