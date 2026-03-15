import cv2
from camera.camera_reader import CameraReader
from core.pipeline import process_frame

def main():

    camera = CameraReader("test_videos/test3.mp4")

    while True:

        frame = camera.read()

        if frame is None:
            break

        frame, detections = process_frame(frame)

        for d in detections:
            x1, y1, x2, y2 = map(int, d["bbox"])
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

        cv2.imshow("VisionIQ", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()