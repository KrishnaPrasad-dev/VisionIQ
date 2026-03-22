import argparse

from app_runner import run_detection_loop


def parse_args():
    parser = argparse.ArgumentParser(description="VisionIQ detection runner")
    parser.add_argument(
        "--source",
        default="test_videos/test3.mp4",
        help="Video source: file path, RTSP URL, or webcam index (e.g. 0)",
    )
    parser.add_argument(
        "--camera-id",
        default="cam_1",
        help="Logical camera id used for behavior baseline profile",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_detection_loop(source=args.source, camera_id=args.camera_id)


if __name__ == "__main__":
    main()