import cv2
import json
import time

from core.pipeline import process_frame, draw_overlay
from core.normal_behavior import normal_behavior_model
from core.rules_engine import RulesEngine
from alerts.alert_manager import alert_manager
from utils.logger import setup_logger


logger = setup_logger("VisionIQ")


def _coerce_source(source):
    if isinstance(source, int):
        return source

    value = str(source).strip()
    if value.isdigit():
        return int(value)
    return value


def run_detection_loop(source, camera_id="cam_1", stop_event=None, on_status=None):
    """Run realtime detection loop for a camera/video source.

    Args:
        source: RTSP URL, file path, or webcam index.
        camera_id: Logical camera id for baseline profile storage.
        stop_event: Optional threading.Event to stop from another thread.
        on_status: Optional callback(status: str, payload: dict).
    """
    src = _coerce_source(source)
    cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        msg = f"Could not open video source: {source}"
        logger.error(msg)
        if on_status:
            on_status("error", {"message": msg})
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = int(1000 / max(fps, 1))

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    process_every_n = 2
    target_height = 480
    scale_factor = min(1.0, target_height / height) if height > target_height else 1.0

    if scale_factor < 1.0:
        original_width = width
        original_height = height
        width = int(width * scale_factor)
        height = int(height * scale_factor)
        logger.info(f"Resolution scaling: {original_width}x{original_height} -> {width}x{height}")

    camera_config = {
        "camera_id": camera_id,
        "zones": [],
        "rules": {
            "maxPeople": 2,
            "restrictedAccess": False,
            "adaptiveLearning": True,
            "mode": "SHOP",
        },
    }

    rules_engine = RulesEngine(camera_config["rules"])

    logger.info("Starting VisionIQ")
    logger.info(f"FPS: {fps} | Resolution: {width}x{height} | Process Every N: {process_every_n}")
    logger.info(f"Config: {json.dumps(camera_config, indent=2)}")
    if on_status:
        on_status(
            "started",
            {
                "source": str(source),
                "fps": float(fps),
                "resolution": f"{width}x{height}",
                "camera_id": camera_id,
            },
        )

    frame_count = 0
    detection_frame_count = 0
    prev_score = 0
    app_start_time = time.time()
    fps_counter = 0
    fps_window_start = time.time()

    last_result = {
        "frame": None,
        "detections": [],
        "people_count": 0,
        "loitering": False,
        "loitering_ids": [],
        "running": False,
        "running_ids": [],
        "score": 0,
        "status": "SAFE",
        "track_stability": 0,
        "zone_hits": [],
    }
    last_events = []

    try:
        while True:
            if stop_event and stop_event.is_set():
                logger.info("Stop requested by desktop app")
                break

            ret, frame = cap.read()
            if not ret:
                logger.info("End of stream or failed frame read")
                break

            frame_count += 1

            if scale_factor < 1.0:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

            should_detect = (frame_count - 1) % process_every_n == 0

            if should_detect:
                detection_frame_count += 1
                result = process_frame(frame, camera_config)
                events = rules_engine.evaluate(result)
                last_result = result
                last_events = events

                current_score = result["score"]
                if alert_manager.should_alert(current_score, prev_score, min_frames_between=30):
                    alert_id = alert_manager.create_alert(frame, result, alert_type="THREAT_DETECTED")
                    logger.warning(f"ALERT: {alert_id} | Score: {current_score} | Status: {result['status']}")
                    if on_status:
                        on_status(
                            "alert",
                            {
                                "alert_id": alert_id,
                                "score": int(current_score),
                                "status": result.get("status", "SAFE"),
                            },
                        )

                prev_score = current_score

            render_result = dict(last_result)
            render_result["frame"] = frame
            display = draw_overlay(frame.copy(), render_result, last_events)

            fps_counter += 1
            elapsed = time.time() - fps_window_start

            if frame_count % 60 == 0:
                current_fps = fps_counter / max(elapsed, 0.001)
                stats = alert_manager.get_stats()
                det_fps = detection_frame_count / max(time.time() - app_start_time, 0.001)
                baseline_samples = last_result.get("baseline_samples", 0)
                logger.info(
                    f"Frame {frame_count} | UI FPS: {current_fps:.1f} | DET FPS: {det_fps:.1f} | "
                    f"Status: {last_result.get('status', 'SAFE')} | Score: {last_result.get('score', 0)} | "
                    f"People: {last_result.get('people_count', 0)} | BaselineSamples: {baseline_samples} | Alerts: {stats['total_alerts']}"
                )
                if on_status:
                    on_status(
                        "heartbeat",
                        {
                            "frame": frame_count,
                            "ui_fps": round(current_fps, 1),
                            "det_fps": round(det_fps, 1),
                            "status": last_result.get("status", "SAFE"),
                            "score": int(last_result.get("score", 0)),
                            "people": int(last_result.get("people_count", 0)),
                        },
                    )
                fps_counter = 0
                fps_window_start = time.time()

            cv2.imshow("VisionIQ - Press ESC to exit", display)

            if cv2.waitKey(frame_delay) == 27:
                logger.info("User exit from OpenCV window")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        normal_behavior_model.flush(camera_config.get("camera_id", "default"))

        final_stats = alert_manager.get_stats()
        total_runtime = max(time.time() - app_start_time, 0.001)
        avg_ui_fps = frame_count / total_runtime
        avg_det_fps = detection_frame_count / total_runtime
        logger.info(
            f"Session ended | Total frames: {frame_count} | Detection frames: {detection_frame_count} | "
            f"Avg UI FPS: {avg_ui_fps:.1f} | Avg DET FPS: {avg_det_fps:.1f} | Total alerts: {final_stats['total_alerts']}"
        )
        if on_status:
            on_status(
                "stopped",
                {
                    "frames": frame_count,
                    "alerts": int(final_stats.get("total_alerts", 0)),
                },
            )
