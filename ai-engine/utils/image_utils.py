import cv2
from config.config import FRAME_WIDTH, FRAME_HEIGHT

def resize_frame(frame):
    return cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))