import asyncio
import base64
from collections import deque
import os
import socket
import threading
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import cv2
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from alerts.alert_manager import alert_manager
from alerts.push_notifier import PushNotifier
from core.normal_behavior import normal_behavior_model
from core.pipeline import draw_overlay, process_frame
from core.rules_engine import RulesEngine
from utils.logger import setup_logger


logger = setup_logger("QuantumEye-Stream")

dashboard_api_url = os.getenv("DASHBOARD_API_URL", "http://localhost:3000")
push_notifier = PushNotifier(api_base_url=dashboard_api_url)

ALERT_COOLDOWN_SEC = int(os.getenv("QUANTUMEYE_ALERT_COOLDOWN_SEC", "300"))
ALERT_MIN_SCORE = int(os.getenv("QUANTUMEYE_ALERT_MIN_SCORE", "60"))
INCIDENT_BUFFER_SEC = int(os.getenv("QUANTUMEYE_INCIDENT_BUFFER_SEC", "8"))


class StartCameraRequest(BaseModel):
    id: Optional[str] = None
    source: str
    rules: Dict[str, Any] = {}


class TestSourceRequest(BaseModel):
    source: str


class UpdateCameraRulesRequest(BaseModel):
    id: str
    rules: Dict[str, Any] = {}


class AckAlertRequest(BaseModel):
    camera_id: str


class StreamEngine:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._camera_lock = threading.Lock()
        self._camera_state: Dict[str, Any] = {
            "camera_id": None,
            "rules": {},
        }
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
            "alerts": [],
            "ts": time.time(),
        }
        self._sequence = 0
        self._alert_gate: Dict[str, Dict[str, float]] = {}

    @staticmethod
    def _coerce_source(source: Any):
        value = str(source).strip()
        return int(value) if value.isdigit() else value

    @staticmethod
    def _normalize_rules(rules: Optional[Dict[str, Any]] = None):
        rules = dict(rules or {})
        max_people = rules.get("maxPeopleAllowed", rules.get("maxPeople"))

        try:
            if max_people in (None, ""):
                max_people = int(os.getenv("QUANTUMEYE_MAX_PEOPLE", "8"))
            else:
                max_people = int(max_people)
        except (TypeError, ValueError):
            max_people = int(os.getenv("QUANTUMEYE_MAX_PEOPLE", "8"))

        restricted_zone = bool(rules.get("restrictedZoneMonitoring") or rules.get("restrictedAccess"))

        return {
            "maxPeople": max_people,
            "maxPeopleAllowed": max_people,
            "restrictedAccess": restricted_zone,
            "restrictedZoneMonitoring": restricted_zone,
            "adaptiveLearning": bool(rules.get("adaptiveLearning", True)),
            "mode": rules.get("mode", "SHOP"),
            "openHoursStart": str(rules.get("openHoursStart") or ""),
            "openHoursEnd": str(rules.get("openHoursEnd") or ""),
            "zoneLabel": str(rules.get("zoneLabel") or ""),
            "notes": str(rules.get("notes") or ""),
        }

    def _set_camera_state(self, camera_id: str, rules: Optional[Dict[str, Any]] = None):
        with self._camera_lock:
            self._camera_state = {
                "camera_id": str(camera_id),
                "rules": self._normalize_rules(rules),
            }

    def _update_camera_rules(self, camera_id: str, rules: Optional[Dict[str, Any]] = None):
        with self._camera_lock:
            active_id = self._camera_state.get("camera_id")
            if active_id is None or str(active_id) != str(camera_id):
                return False

            current_rules = dict(self._camera_state.get("rules") or {})
            current_rules.update(self._normalize_rules(rules))
            self._camera_state["rules"] = current_rules
            return True

    def _get_camera_state(self):
        with self._camera_lock:
            return {
                "camera_id": self._camera_state.get("camera_id"),
                "rules": dict(self._camera_state.get("rules") or {}),
            }

    def _gate(self, camera_id: str):
        gate = self._alert_gate.get(camera_id)
        if gate is None:
            gate = {
                "last_alert_ts": 0.0,
                "last_ack_ts": 0.0,
                "last_alert_score": 0.0,
            }
            self._alert_gate[camera_id] = gate
        return gate

    def acknowledge_alert(self, camera_id: str):
        gate = self._gate(str(camera_id))
        gate["last_ack_ts"] = time.time()

    @staticmethod
    def _serialize_alerts(camera_id: str, limit: int = 80):
        history = alert_manager.get_alert_history(limit=limit)
        items = []
        for alert in history:
            record_camera_id = str(alert.get("camera_id") or "")
            if record_camera_id and record_camera_id != str(camera_id):
                continue

            items.append(
                {
                    "id": alert.get("id"),
                    "timestamp": alert.get("timestamp"),
                    "status": alert.get("threat_status", "INFO"),
                    "score": int(alert.get("threat_score", 0)),
                    "person_count": int(alert.get("people_count", 0)),
                    "playback_path": alert.get("playback_path"),
                    "snapshot_path": alert.get("snapshot_path"),
                }
            )
        return items

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

    def start(self, source: str, camera_id: str, rules: Optional[Dict[str, Any]] = None):
        self.stop()
        self._set_camera_state(camera_id, rules)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(source, camera_id, self._stop_event),
            daemon=True,
        )
        self._thread.start()

    def test_source(self, source: str):
        """Validate a source without changing the current running stream."""
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
        fps_value = max(float(fps or 15), 1.0)
        frame_buffer = deque(maxlen=max(10, int(fps_value * INCIDENT_BUFFER_SEC)))

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
                camera_state = self._get_camera_state()
                camera_config = {
                    "camera_id": camera_id,
                    "zones": [],
                    "rules": camera_state.get("rules", {}),
                }
                rules_engine = RulesEngine(camera_config["rules"])

                result = process_frame(frame, camera_config)
                events = rules_engine.evaluate(result)
                display = draw_overlay(frame.copy(), result, events)
                frame_buffer.append(display.copy())

                now = time.time()
                gate = self._gate(str(camera_id))
                alert_score = int(result.get("score", 0))
                has_breach_signal = bool(result.get("zone_hits")) or bool(result.get("after_hours"))
                should_consider_alert = alert_score >= ALERT_MIN_SCORE and (has_breach_signal or result.get("status") == "CRITICAL")
                can_alert_by_cooldown = (now - gate["last_alert_ts"]) >= ALERT_COOLDOWN_SEC
                acknowledged_since_last = gate["last_ack_ts"] > gate["last_alert_ts"]

                if should_consider_alert and (can_alert_by_cooldown or acknowledged_since_last):
                    alert_id = alert_manager.create_alert(
                        frame=display,
                        result=result,
                        alert_type="THREAT_DETECTED",
                        clip_frames=list(frame_buffer),
                        fps=fps_value,
                        camera_id=str(camera_id),
                    )
                    gate["last_alert_ts"] = now
                    gate["last_alert_score"] = alert_score
                    logger.warning("ALERT: %s | Score: %s | Status: %s", alert_id, alert_score, result.get("status"))

                    try:
                        push_notifier.notify_alert(
                            alert_type="THREAT_DETECTED",
                            threat_score=alert_score,
                            camera_id=str(camera_id),
                            message=f"Threat detected: {result.get('status', 'UNKNOWN')} (Score: {alert_score})",
                            deep_link="/alerts",
                        )
                    except Exception as push_err:
                        logger.error("Failed to send push notification: %s", push_err)

                ok, encoded = cv2.imencode(
                    ".jpg", display, [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                )
                if not ok:
                    continue

                annotated_base64 = base64.b64encode(encoded.tobytes()).decode("ascii")

                self._update_payload(
                    {
                        "status": "running",
                        "message": "Camera stream active",
                        "annotated_base64": annotated_base64,
                        "threat_score": int(result.get("score", 0)),
                        "person_count": int(result.get("people_count", 0)),
                        "loitering_count": len(result.get("loitering_ids", [])),
                        "zone_triggered": len(result.get("zone_hits", [])) > 0,
                        "after_hours": bool(result.get("after_hours", False)),
                        "camera_id": camera_id,
                        "source": str(source),
                        "effective_source": effective_source,
                        "events": events,
                        "alerts": self._serialize_alerts(str(camera_id), limit=80),
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/alerts",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "alerts")),
    name="alerts",
)

engine = StreamEngine()


@app.get("/health")
def health():
    seq, payload = engine.get_payload()
    return {"ok": True, "sequence": seq, "state": payload.get("status")}


@app.post("/start-camera")
def start_camera(req: StartCameraRequest):
    camera_id = req.id or "cam_1"
    engine.start(source=req.source, camera_id=str(camera_id), rules=req.rules)
    return {
        "success": True,
        "message": "Camera stream started",
        "camera_id": str(camera_id),
        "source": req.source,
    }


@app.post("/update-camera-rules")
def update_camera_rules(req: UpdateCameraRulesRequest):
    updated = engine._update_camera_rules(req.id, req.rules)
    return {
        "success": True,
        "updated": updated,
        "camera_id": req.id,
    }


@app.post("/ack-alert")
def ack_alert(req: AckAlertRequest):
    engine.acknowledge_alert(req.camera_id)
    return {"success": True, "camera_id": req.camera_id}


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
