import cv2
import json
from datetime import datetime
from pathlib import Path


AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent


class AlertManager:
    """Manages alert history, incident playback clips, and cloud sync queue."""

    def __init__(
        self,
        base_path="alerts",
        incident_quality=65,
        media_max_width=960,
        max_incident_files=300,
        max_history_files=2000,
    ):
        self.base_path = (AI_ENGINE_ROOT / base_path).resolve()
        self.incidents_path = self.base_path / "incidents"
        self.history_path = self.base_path / "history"
        self.queue_path = self.base_path / "queue"
        self.incident_quality = int(incident_quality)
        self.media_max_width = int(media_max_width)
        self.max_incident_files = int(max_incident_files)
        self.max_history_files = int(max_history_files)
        
        # Create directories
        for path in [self.incidents_path, self.history_path, self.queue_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.alert_history = []
        self.frame_count = 0
        self.last_alert_frame = -100  # Debounce alerts

    def _compress_frame(self, frame):
        """Downscale large frames before writing media files."""
        h, w = frame.shape[:2]
        if w <= self.media_max_width:
            return frame

        scale = self.media_max_width / float(w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def _write_incident_clip(self, alert_id, clip_frames=None, fps=15):
        frames = list(clip_frames or [])
        if not frames:
            return None

        prepared = [self._compress_frame(frame) for frame in frames if frame is not None]
        if not prepared:
            return None

        first = prepared[0]
        h, w = first.shape[:2]
        output_path = self.incidents_path / f"{alert_id}.mp4"
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            max(6.0, min(float(fps or 15), 30.0)),
            (w, h),
        )

        if not writer.isOpened():
            return None

        try:
            for frame in prepared:
                if frame.shape[1] != w or frame.shape[0] != h:
                    frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
                writer.write(frame)
        finally:
            writer.release()

        return output_path

    def _cleanup_by_count(self, folder_path, pattern, keep_count):
        files = sorted(folder_path.glob(pattern), key=lambda p: p.stat().st_mtime)
        overflow = len(files) - int(keep_count)
        if overflow <= 0:
            return
        for old_file in files[:overflow]:
            old_file.unlink(missing_ok=True)
        
    def should_alert(self, current_score, prev_score=0, min_frames_between=30):
        """
        Determine if alert should be triggered
        
        Debounces alerts to prevent spam
        """
        self.frame_count += 1
        
        # Check if enough frames have passed since last alert
        if self.frame_count - self.last_alert_frame < min_frames_between:
            return False
        
        # Alert on significant score increase or critical threshold
        if current_score >= 60 or (current_score >= 40 and current_score > prev_score + 15):
            self.last_alert_frame = self.frame_count
            return True
        
        return False
    
    def create_alert(self, frame, result, alert_type="THREAT_DETECTED", clip_frames=None, fps=15, camera_id=None):
        """
        Create and save alert with incident playback clip
        
        Returns: alert_id for tracking
        """
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        clip_source = list(clip_frames or [])
        if frame is not None:
            clip_source.append(frame)
        incident_path = self._write_incident_clip(alert_id, clip_frames=clip_source, fps=fps)
        
        # Create alert record
        playback_path = None
        if incident_path:
            try:
                playback_path = str(incident_path.relative_to(AI_ENGINE_ROOT)).replace("\\", "/")
            except Exception:
                playback_path = str(incident_path).replace("\\", "/")

        alert_record = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "camera_id": str(camera_id) if camera_id is not None else None,
            "threat_score": result.get("score", 0),
            "threat_status": result.get("status", "UNKNOWN"),
            "people_count": result.get("people_count", 0),
            "loitering_detected": result.get("loitering", False),
            "zone_hits": result.get("zone_hits", []),
            "playback_path": playback_path,
            "snapshot_path": None,
            "uploaded": False
        }
        
        # Add to history
        self.alert_history.append(alert_record)
        
        # Save to disk
        history_file = self.history_path / f"{alert_id}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(alert_record, f, separators=(",", ":"))
        
        # Add to cloud sync queue
        queue_file = self.queue_path / f"{alert_id}.json"
        with open(queue_file, 'w', encoding='utf-8') as f:
            json.dump(alert_record, f, separators=(",", ":"))

        # Retention cleanup to prevent buildup
        self._cleanup_by_count(self.incidents_path, "*.mp4", self.max_incident_files)
        self._cleanup_by_count(self.history_path, "*.json", self.max_history_files)
        
        return alert_id
    
    def get_alert_history(self, limit=50):
        """Get recent alerts"""
        return self.alert_history[-limit:][::-1]
    
    def get_pending_uploads(self):
        """Get alerts waiting to be uploaded to cloud"""
        pending = []
        for file in self.queue_path.glob("*.json"):
            with open(file, 'r') as f:
                alert = json.load(f)
                pending.append(alert)
        return pending
    
    def mark_uploaded(self, alert_id):
        """Mark alert as uploaded to cloud"""
        queue_file = self.queue_path / f"{alert_id}.json"
        
        if queue_file.exists():
            queue_file.unlink()
        
        # Update history
        history_file = self.history_path / f"{alert_id}.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                alert = json.load(f)
            
            alert["uploaded"] = True
            with open(history_file, 'w') as f:
                json.dump(alert, f, indent=2)
    
    def cleanup_old_snapshots(self, days=7):
        """Delete old incident clips to save space (legacy method name)."""
        import time
        current_time = time.time()
        max_age = days * 24 * 3600
        
        deleted_count = 0
        for clip in self.incidents_path.glob("*.mp4"):
            if current_time - clip.stat().st_mtime > max_age:
                clip.unlink()
                deleted_count += 1
        
        return deleted_count
    
    def get_stats(self):
        """Get alert statistics"""
        return {
            "total_alerts": len(self.alert_history),
            "pending_uploads": len(self.get_pending_uploads()),
            "incident_clips_count": len(list(self.incidents_path.glob("*.mp4"))),
            "frames_processed": self.frame_count
        }


# Global alert manager instance
alert_manager = AlertManager("alerts")
