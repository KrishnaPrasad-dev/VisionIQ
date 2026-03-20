import cv2

from core.pipeline import process_frame, draw_overlay
from core.rules_engine import RulesEngine


def main():

    cap = cv2.VideoCapture("test_videos/test3.mp4")

    if not cap.isOpened():
        print("Could not open video source")
        return

    camera_config = {
        "camera_id": "cam_1",
        "zones": [],
        "rules": {
            "maxPeople": 2,
            "restrictedAccess": False
        }
    }

    rules_engine = RulesEngine(camera_config["rules"])

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        result = process_frame(frame, camera_config)
        events = rules_engine.evaluate(result)

        display = draw_overlay(result["frame"], result, events)

        cv2.imshow("VisionIQ", display)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()