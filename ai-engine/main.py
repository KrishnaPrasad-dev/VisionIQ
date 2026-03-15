import cv2
from core.pipeline import process_frame


def main():

    # change this to your video file or webcam
    cap = cv2.VideoCapture("test_videos/test.mp4")
    # for webcam use: cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Could not open video source")
        return

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        annotated, score, status = process_frame(frame)

        cv2.imshow("VisionIQ", annotated)

        key = cv2.waitKey(1)

        if key == 27:   # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()