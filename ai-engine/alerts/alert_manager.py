import cv2
import os
import json
from datetime import datetime
from pathlib import Path


class AlertManager:
    """Manages alert history, snapshots, and cloud sync queue"""
    
    def __init__(self, base_path="alerts"):
        self.base_path = Path(base_path)
        self.snapshots_path = self.base_path / "snapshots"
        self.history_path = self.base_path / "history"
        self.queue_path = self.base_path / "queue"
        
        # Create directories
        for path in [self.snapshots_path, self.history_path, self.queue_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.alert_history = []
        self.frame_count = 0
        self.last_alert_frame = -100  # Debounce alerts
        
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
    
    def create_alert(self, frame, result, alert_type="THREAT_DETECTED"):
        """
        Create and save alert with snapshot
        
        Returns: alert_id for tracking
        """
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Save snapshot
        snapshot_path = self.snapshots_path / f"{alert_id}.jpg"
        success = cv2.imwrite(
            str(snapshot_path),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 85]  # 85% quality to save space
        )
        
        # Create alert record
        alert_record = {
            "id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "threat_score": result.get("score", 0),
            "threat_status": result.get("status", "UNKNOWN"),
            "people_count": result.get("people_count", 0),
            "loitering_detected": result.get("loitering", False),
            "zone_hits": result.get("zone_hits", []),
            "snapshot_path": str(snapshot_path) if success else None,
            "uploaded": False
        }
        
        # Add to history
        self.alert_history.append(alert_record)
        
        # Save to disk
        history_file = self.history_path / f"{alert_id}.json"
        with open(history_file, 'w') as f:
            json.dump(alert_record, f, indent=2)
        
        # Add to cloud sync queue
        queue_file = self.queue_path / f"{alert_id}.json"
        with open(queue_file, 'w') as f:
            json.dump(alert_record, f, indent=2)
        
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
        """Delete old snapshots to save space"""
        import time
        current_time = time.time()
        max_age = days * 24 * 3600
        
        deleted_count = 0
        for snapshot in self.snapshots_path.glob("*.jpg"):
            if current_time - snapshot.stat().st_mtime > max_age:
                snapshot.unlink()
                deleted_count += 1
        
        return deleted_count
    
    def get_stats(self):
        """Get alert statistics"""
        return {
            "total_alerts": len(self.alert_history),
            "pending_uploads": len(self.get_pending_uploads()),
            "snapshots_count": len(list(self.snapshots_path.glob("*.jpg"))),
            "frames_processed": self.frame_count
        }


# Global alert manager instance
alert_manager = AlertManager("alerts")
