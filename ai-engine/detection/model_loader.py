from ultralytics import YOLO
from config.config import MODEL_PATH

model = None

def load_model():
    global model
    if model is None:
        print("Loading YOLO model...")
        model = YOLO(MODEL_PATH)
    return model