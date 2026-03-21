import cv2
import json
import time

from core.pipeline import process_frame, draw_overlay
from core.normal_behavior import normal_behavior_model
from core.rules_engine import RulesEngine
from alerts.alert_manager import alert_manager
from utils.logger import setup_logger

logger = setup_logger("VisionIQ")


def main():

    cap = cv2.VideoCapture("test_videos/test3.mp4")

    if not cap.isOpened():
        logger.error("Could not open video source")
        return

    # Get video properties for display
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = int(1000 / fps)
    
    # Get resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Process every Nth frame to keep UI smooth on CPU-only systems.
    PROCESS_EVERY_N = 2
    
    # Resolution scaling (auto-reduce if needed)
    TARGET_HEIGHT = 480  # Reduce to 480p if input is larger
    scale_factor = min(1.0, TARGET_HEIGHT / height) if height > TARGET_HEIGHT else 1.0
    
    if scale_factor < 1.0:
        width = int(width * scale_factor)
        height = int(height * scale_factor)
        logger.info(f"Resolution scaling: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))} -> {width}x{height}")

    camera_config = {
        "camera_id": "cam_1",
        "zones": [],
        "rules": {
            "maxPeople": 2,
            "restrictedAccess": False,
            "adaptiveLearning": True,
            "mode": "SHOP",
        }
    }

    rules_engine = RulesEngine(camera_config["rules"])
    
    logger.info(f"Starting VisionIQ")
    logger.info(f"FPS: {fps} | Resolution: {width}x{height} | Process Every N: {PROCESS_EVERY_N}")
    logger.info(f"Config: {json.dumps(camera_config, indent=2)}")

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

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Resize frame for performance
        if scale_factor < 1.0:
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

        should_detect = (frame_count - 1) % PROCESS_EVERY_N == 0
        
        if should_detect:
            detection_frame_count += 1
            
            result = process_frame(frame, camera_config)
            events = rules_engine.evaluate(result)
            last_result = result
            last_events = events

            current_score = result["score"]

            # Check if alert should be triggered
            if alert_manager.should_alert(current_score, prev_score, min_frames_between=30):
                alert_id = alert_manager.create_alert(frame, result, alert_type="THREAT_DETECTED")
                logger.warning(f"ALERT: {alert_id} | Score: {current_score} | Status: {result['status']}")

            prev_score = current_score

        # Reuse latest detections on skipped frames for smooth display.
        render_result = dict(last_result)
        render_result["frame"] = frame
        display = draw_overlay(frame.copy(), render_result, last_events)

        # FPS counter
        fps_counter += 1
        elapsed = time.time() - fps_window_start
        
        # Log every 60 frames
        if frame_count % 60 == 0:
            current_fps = fps_counter / elapsed
            stats = alert_manager.get_stats()
            det_fps = detection_frame_count / max(time.time() - app_start_time, 0.001)
            baseline_samples = last_result.get("baseline_samples", 0)
            logger.info(
                f"Frame {frame_count} | UI FPS: {current_fps:.1f} | DET FPS: {det_fps:.1f} | "
                f"Status: {last_result.get('status', 'SAFE')} | Score: {last_result.get('score', 0)} | "
                f"People: {last_result.get('people_count', 0)} | BaselineSamples: {baseline_samples} | Alerts: {stats['total_alerts']}"
            )
            fps_counter = 0
            fps_window_start = time.time()

        # Display
        cv2.imshow("VisionIQ - Press ESC to exit", display)

        if cv2.waitKey(frame_delay) == 27:  # ESC key
            logger.info("User exit")
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    normal_behavior_model.flush(camera_config.get("camera_id", "default"))
    
    # Final stats
    final_stats = alert_manager.get_stats()
    total_runtime = max(time.time() - app_start_time, 0.001)
    avg_ui_fps = frame_count / total_runtime
    avg_det_fps = detection_frame_count / total_runtime
    logger.info(
        f"Session ended | Total frames: {frame_count} | Detection frames: {detection_frame_count} | "
        f"Avg UI FPS: {avg_ui_fps:.1f} | Avg DET FPS: {avg_det_fps:.1f} | Total alerts: {final_stats['total_alerts']}"
    )


if __name__ == "__main__":
    main()