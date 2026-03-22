import argparse
import os

import requests

from app_runner import run_detection_loop


def _require_token(args):
    token = args.token or os.getenv("VISIONIQ_TOKEN")
    if not token:
        raise ValueError("Missing token. Pass --token or set VISIONIQ_TOKEN")
    return token


def _fetch_user_cameras(api_base, token):
    base = api_base.rstrip("/")
    response = requests.get(
        f"{base}/api/cameras",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON response from {base}/api/cameras") from exc

    if not response.ok or not payload.get("success"):
        error = payload.get("error") if isinstance(payload, dict) else None
        raise RuntimeError(error or f"Camera fetch failed with HTTP {response.status_code}")

    cameras = payload.get("cameras", [])
    if not cameras:
        raise RuntimeError("No cameras found for this user account")
    return cameras


def _select_camera(cameras, camera_id=None, camera_name=None, camera_index=0):
    if camera_id:
        for camera in cameras:
            if str(camera.get("_id")) == str(camera_id):
                return camera
        raise RuntimeError(f"Camera id not found: {camera_id}")

    if camera_name:
        for camera in cameras:
            if str(camera.get("name", "")).strip().lower() == str(camera_name).strip().lower():
                return camera
        raise RuntimeError(f"Camera name not found: {camera_name}")

    if camera_index < 0 or camera_index >= len(cameras):
        raise RuntimeError(f"Camera index out of range: {camera_index}. Available: 0..{len(cameras) - 1}")
    return cameras[camera_index]


def resolve_source_and_camera_id(args):
    if args.source:
        return args.source, args.camera_id

    token = _require_token(args)
    cameras = _fetch_user_cameras(args.api_base, token)
    camera = _select_camera(
        cameras,
        camera_id=args.website_camera_id,
        camera_name=args.website_camera_name,
        camera_index=args.website_camera_index,
    )

    source = camera.get("source")
    if source is None or str(source).strip() == "":
        raise RuntimeError("Selected website camera has empty source")

    resolved_camera_id = args.camera_id or str(camera.get("_id") or "cam_1")
    print(
        f"Using website camera: name='{camera.get('name', 'Unnamed')}', "
        f"id='{camera.get('_id')}', type='{camera.get('type', 'rtsp')}'"
    )
    return source, resolved_camera_id


def parse_args():
    parser = argparse.ArgumentParser(description="VisionIQ detection runner")
    parser.add_argument(
        "--source",
        default=None,
        help="Direct source override: file path, RTSP URL, or webcam index (e.g. 0)",
    )
    parser.add_argument(
        "--camera-id",
        default=None,
        help="Logical camera id used for behavior baseline profile",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:3000",
        help="Website base URL for fetching user cameras",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="JWT from website login API. Falls back to VISIONIQ_TOKEN env var",
    )
    parser.add_argument(
        "--website-camera-id",
        default=None,
        help="Select website camera by Mongo _id",
    )
    parser.add_argument(
        "--website-camera-name",
        default=None,
        help="Select website camera by exact camera name (case-insensitive)",
    )
    parser.add_argument(
        "--website-camera-index",
        type=int,
        default=0,
        help="Select website camera by index from /api/cameras response (default: 0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    source, camera_id = resolve_source_and_camera_id(args)
    run_detection_loop(source=source, camera_id=camera_id)


if __name__ == "__main__":
    main()