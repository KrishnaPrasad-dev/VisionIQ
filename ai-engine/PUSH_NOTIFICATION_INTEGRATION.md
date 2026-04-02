"""
Integration example: Using push notifications in the alert system

This module demonstrates how to integrate push notifications alongside
existing WebSocket alert emission in the VisionIQ stream engine.
"""

from alerts.push_notifier import notify_alert
import logging


logger = logging.getLogger(__name__)


def emit_alert_with_push(
    websocket_manager,  # Your existing WebSocket manager
    alert_type: str,
    threat_score: float,
    camera_id: str,
    frame_data: dict,
    result_data: dict = None,
) -> dict:
    """
    Emit alert via both WebSocket and push notification
    
    This function demonstrates how to add push notifications alongside
    existing WebSocket alerts without replacing them.
    
    Args:
        websocket_manager: Your existing WebSocket connection manager
        alert_type: Type of alert (e.g., "THREAT_DETECTED")
        threat_score: Threat score 0-100
        camera_id: Camera identifier
        frame_data: Frame information for WebSocket emission
        result_data: Additional result data for the alert
    
    Returns:
        dict with emission results
    """
    
    # 1. EXISTING CODE: Emit alert via WebSocket
    # This continues to work as before - DO NOT REPLACE THIS
    websocket_payload = {
        "event": "alert",
        "type": alert_type,
        "threat_score": threat_score,
        "camera_id": camera_id,
        "timestamp": frame_data.get("ts"),
        **result_data or {}
    }
    
    try:
        websocket_manager.broadcast(websocket_payload)
        logger.info(f"Alert emitted to {len(websocket_manager.connections)} connected clients via WebSocket")
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {e}")
    
    # 2. NEW CODE: Send push notification alongside WebSocket
    # This adds browser push notifications - no WebSocket replacement
    try:
        # Determine message based on threat level
        message = None
        if threat_score >= 75:
            message = f"CRITICAL: {alert_type} with score {int(threat_score)}"
        elif threat_score >= 45:
            message = f"Suspicious: {alert_type} detected"
        else:
            message = f"{alert_type} detected"
        
        # Send push notification
        push_result = notify_alert(
            alert_type=alert_type,
            threat_score=threat_score,
            camera_id=camera_id,
            message=message,
            deep_link="/dashboard",
            api_base_url="http://localhost:3000"  # Match your config
        )
        
        if push_result.get("success"):
            logger.info(f"Push notifications sent: {push_result.get('sent', 0)}/{push_result.get('total', 0)}")
        else:
            logger.warning(f"Push notification failed: {push_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        # Don't let push errors break WebSocket alerts
    
    return {
        "websocket_emitted": True,
        "push_sent": push_result.get("success", False) if 'push_result' in locals() else False
    }


# Integration points in stream_server.py
# ========================================

"""
Example integration in stream_server.py:

from alerts.push_notifier import notify_alert


class StreamEngine:
    def _process_alert(self, result, frame, camera_id):
        '''
        Existing alert processing - add push notification here
        '''
        
        alert_type = "THREAT_DETECTED"
        threat_score = result.get("score", 0)
        
        # ... existing code ...
        
        # EXISTING: Emit via WebSocket
        await self.websocket_manager.broadcast({...})
        
        # NEW: Add push notification
        notify_alert(
            alert_type=alert_type,
            threat_score=threat_score,
            camera_id=camera_id,
            message=f"Threat score: {int(threat_score)}",
            api_base_url=os.getenv("DASHBOARD_API_URL", "http://localhost:3000")
        )
"""


# Example: Usage in alert_manager.py
# ====================================

"""
from alerts.push_notifier import notify_alert


class AlertManager:
    def create_alert(self, frame, result, alert_type="THREAT_DETECTED"):
        '''
        Existing create_alert method - add push notification after alert creation
        '''
        
        # ... existing alert creation code ...
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # ... save snapshot, create record ...
        alert_record = {...}
        
        # NEW: Send push notification
        threat_score = result.get("score", 0)
        if threat_score >= 40:  # Only notify on significant threats
            notify_alert(
                alert_type=alert_type,
                threat_score=threat_score,
                camera_id=self.camera_id,
                message=f"Alert: {alert_type} detected"
            )
        
        return alert_id
"""
