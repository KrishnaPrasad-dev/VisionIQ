import base64
import asyncio
import os
import socket
import threading
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import cv2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.normal_behavior import normal_behavior_model
from core.pipeline import draw_overlay, process_frame
from core.rules_engine import RulesEngine
from utils.logger import setup_logger


logger = setup_logger("QuantumEye-Stream")


class StartCameraRequest(BaseModel):
    id: Optional[str] = None
    source: str


class TestSourceRequest(BaseModel):
    source: str


class StreamEngine:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._latest_payload: Dict[str, Any] = {
            "status": "idle",
            "message": "Waiting for camera start",
            "annotated_base64": None,
            "threat_score": 0,
            "person_count": 0,
            "loitering_count": 0,
            "zone_triggered": False,
            "after_hours": False,
            "camera_id": None,
            "source": None,
            "ts": time.time(),
        }
        self._sequence = 0

    @staticmethod
    def _coerce_source(source: Any):
        value = str(source).strip()
        return int(value) if value.isdigit() else value

    def get_payload(self):
        with self._state_lock:
            return self._sequence, dict(self._latest_payload)

    def _update_payload(self, patch: Dict[str, Any]):
        with self._state_lock:
            self._latest_payload.update(patch)
            self._latest_payload["ts"] = time.time()
            self._sequence += 1

    def _open_capture_with_timeout(self, src: Any, timeout_sec: float = 8.0):
        result: Dict[str, Any] = {}

        def _worker():
            cap = cv2.VideoCapture(src)
            result["cap"] = cap
            result["opened"] = bool(cap.isOpened())

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=timeout_sec)

        if t.is_alive():
            return None, "timeout"

        cap = result.get("cap")
        opened = bool(result.get("opened", False))
        if not cap or not opened:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            return None, "failed"

        return cap, None

    @staticmethod
    def _is_rtsp_tcp_reachable(rtsp_url: str, timeout_sec: float = 2.0):
        try:
            parsed = urlparse(rtsp_url)
            host = parsed.hostname
            port = parsed.port or 554
            if not host:
                return False
            with socket.create_connection((host, port), timeout=timeout_sec):
                return True
        except Exception:
            return False

    def start(self, source: str, camera_id: str):
        self.stop()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(source, camera_id, self._stop_event),
            daemon=True,
        )
        self._thread.start()

    def test_source(self, source: str):
        """Validate a source without changing current running stream."""
        if str(source).strip().lower().startswith("rtsp://"):
            os.environ.setdefault(
                "OPENCV_FFMPEG_CAPTURE_OPTIONS",
                "rtsp_transport;tcp|stimeout;5000000",
            )

        src = self._coerce_source(source)
        is_rtsp_source = str(source).strip().lower().startswith("rtsp://")

        if is_rtsp_source:
            if self._is_rtsp_tcp_reachable(str(source), timeout_sec=2.0):
                cap, open_error = self._open_capture_with_timeout(src, timeout_sec=8.0)
            else:
                cap, open_error = None, "tcp-unreachable"
        else:
            cap = cv2.VideoCapture(src)
            open_error = None if cap.isOpened() else "failed"
            if not cap.isOpened():
                cap.release()
                cap = None

        if cap is None:
            return {
                "ok": False,
                "message": f"Could not open source: {source}",
                "error": open_error,
            }

        try:
            ok, _ = cap.read()
            if not ok:
                return {
                    "ok": False,
                    "message": "Source opened but no frame received",
                    "error": "no-frame",
                }
        finally:
            cap.release()

        return {
            "ok": True,
            "message": "Source reachable",
            "error": None,
        }

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=5)
        self._thread = None

    def _run(self, source: str, camera_id: str, stop_event: threading.Event):
        self._update_payload(
            {
                "status": "connecting",
                "message": "Connecting to camera source",
                "camera_id": camera_id,
                "source": str(source),
            }
        )

        if str(source).strip().lower().startswith("rtsp://"):
            # Keep RTSP dial timeout short so unreachable links fail fast.
            os.environ.setdefault(
                "OPENCV_FFMPEG_CAPTURE_OPTIONS",
                "rtsp_transport;tcp|stimeout;5000000",
            )

        src = self._coerce_source(source)
        is_rtsp_source = str(source).strip().lower().startswith("rtsp://")
        if is_rtsp_source:
            if self._is_rtsp_tcp_reachable(str(source), timeout_sec=2.0):
                cap, open_error = self._open_capture_with_timeout(src, timeout_sec=8.0)
            else:
                cap, open_error = None, "tcp-unreachable"
        else:
            cap = cv2.VideoCapture(src)
            open_error = None if cap.isOpened() else "failed"
            if not cap.isOpened():
                cap.release()
                cap = None
        effective_source = str(source)

        if cap is None:
            demo_video = os.path.join(os.path.dirname(__file__), "test_videos", "test3.mp4")
            should_fallback = (
                is_rtsp_source
                and os.path.exists(demo_video)
                and os.getenv("QUANTUMEYE_RTSP_FALLBACK", "0") == "1"
            )

            if should_fallback:
                logger.warning(
                    "RTSP source unavailable (%s). Falling back to local demo video for live dashboard output",
                    open_error,
                )
                cap = cv2.VideoCapture(demo_video)
                if cap.isOpened():
                    effective_source = demo_video
                    self._update_payload(
                        {
                            "status": "running",
                            "message": "RTSP unreachable. Showing demo fallback stream",
                            "camera_id": camera_id,
                            "source": str(source),
                            "effective_source": effective_source,
                        }
                    )
                else:
                    msg = f"Could not open video source: {source}"
                    cap.release()
                    logger.error("Fallback video failed to open")
                    logger.error(msg)
                    self._update_payload(
                        {
                            "status": "error",
                            "message": msg,
                            "annotated_base64": None,
                            "threat_score": 0,
                            "person_count": 0,
                            "loitering_count": 0,
                            "zone_triggered": False,
                            "after_hours": False,
                            "camera_id": camera_id,
                            "source": str(source),
                        }
                    )
                    return
            else:
                msg = f"Could not open video source: {source}"
                logger.error(msg)
                self._update_payload(
                    {
                        "status": "error",
                        "message": msg,
                        "annotated_base64": None,
                        "threat_score": 0,
                        "person_count": 0,
                        "loitering_count": 0,
                        "zone_triggered": False,
                        "after_hours": False,
                        "camera_id": camera_id,
                        "source": str(source),
                    }
                )
                return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps is None or fps <= 0:
            fps = 15
        frame_interval = max(1.0 / float(fps), 0.03)

        camera_config = {
            "camera_id": camera_id,
            "zones": [],
            "rules": {
                "maxPeople": int(os.getenv("QUANTUMEYE_MAX_PEOPLE", "8")),
                "restrictedAccess": False,
                "adaptiveLearning": True,
                "mode": "SHOP",
            },
        }
        rules_engine = RulesEngine(camera_config["rules"])

        logger.info(f"Stream engine started | camera_id={camera_id} | source={source}")
        self._update_payload(
            {
                "status": "running",
                "message": "Camera stream active",
                "camera_id": camera_id,
                "source": str(source),
                "effective_source": effective_source,
            }
        )

        frame_count = 0

        try:
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    msg = "Failed to read frame from source"
                    self._update_payload(
                        {
                            "status": "error",
                            "message": msg,
                            "annotated_base64": None,
                            "camera_id": camera_id,
                            "source": str(source),
                            "effective_source": effective_source,
                        }
                    )
                    logger.warning(msg)
                    break

                frame_count += 1
                result = process_frame(frame, camera_config)
                events = rules_engine.evaluate(result)
                display = draw_overlay(frame.copy(), result, events)

                ok, encoded = cv2.imencode(
                    ".jpg", display, [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                )
                if not ok:
                    continue

                annotated_base64 = base64.b64encode(encoded.tobytes()).decode("ascii")
                zone_triggered = len(result.get("zone_hits", [])) > 0

                self._update_payload(
                    {
                        "status": "running",
                        "message": "Camera stream active",
                        "annotated_base64": annotated_base64,
                        "threat_score": int(result.get("score", 0)),
                        "person_count": int(result.get("people_count", 0)),
                        "loitering_count": len(result.get("loitering_ids", [])),
                        "zone_triggered": zone_triggered,
                        "after_hours": False,
                        "camera_id": camera_id,
                        "source": str(source),
                        "effective_source": effective_source,
                        "events": events,
                        "frame": frame_count,
                    }
                )

                time.sleep(frame_interval)

        finally:
            cap.release()
            normal_behavior_model.flush(camera_id)
            logger.info("Stream engine stopped")
            self._update_payload(
                {
                    "status": "stopped",
                    "message": "Camera stream stopped",
                    "annotated_base64": None,
                    "camera_id": camera_id,
                    "source": str(source),
                    "effective_source": effective_source,
                }
            )


app = FastAPI(title="QuantumEye Stream Service")
engine = StreamEngine()


@app.get("/health")
def health():
    seq, payload = engine.get_payload()
    return {"ok": True, "sequence": seq, "state": payload.get("status")}


@app.post("/start-camera")
def start_camera(req: StartCameraRequest):
    camera_id = req.id or "cam_1"
    engine.start(source=req.source, camera_id=str(camera_id))
    return {
        "success": True,
        "message": "Camera stream started",
        "camera_id": str(camera_id),
        "source": req.source,
    }


@app.post("/test-source")
def test_source(req: TestSourceRequest):
    result = engine.test_source(source=req.source)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/stop-camera")
def stop_camera():
    engine.stop()
    return {"success": True, "message": "Camera stream stopped"}


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    last_seq = -1

    try:
        while True:
            seq, payload = engine.get_payload()

            if seq != last_seq:
                await websocket.send_json(payload)
                last_seq = seq
            await asyncio.sleep(0.08)

    except WebSocketDisconnect:
        return
    except Exception as exc:
        logger.warning(f"WebSocket closed: {exc}")


@app.on_event("startup")
def startup_event():
    default_source = os.getenv("QUANTUMEYE_SOURCE")
    if default_source:
        logger.info("Auto-starting default source from QUANTUMEYE_SOURCE")
        engine.start(source=default_source, camera_id="cam_1")


@app.on_event("shutdown")
def shutdown_event():
    engine.stop()
