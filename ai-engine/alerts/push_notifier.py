"""
Push notification helper for VisionIQ AI Engine

This module provides utilities to send push notifications from the Python backend
to subscribed browser clients.

Usage:
    from alerts.push_notifier import notify_alert
    
    notify_alert(
        alert_type="THREAT_DETECTED",
        threat_score=75,
        camera_id="cam_1",
        message="Suspicious activity detected"
    )
"""

import requests
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class PushNotifier:
    """Send push notifications from Python backend to dashboard subscribers"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_url = api_base_url.rstrip("/")
        self.alert_endpoint = f"{self.api_url}/api/push/alert"
    
    def notify_alert(
        self,
        alert_type: str,
        threat_score: float,
        camera_id: str = "unknown",
        message: Optional[str] = None,
        deep_link: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: float = 3.0,
    ) -> dict:
        """
        Send push notification for an alert
        
        Args:
            alert_type: Type of alert (e.g., "THREAT_DETECTED", "ZONE_BREACH")
            threat_score: Threat score 0-100
            camera_id: Camera identifier
            message: Custom message (optional)
            deep_link: URL to open on notification click (optional)
            user_id: Specific user to notify (optional, broadcasts if None)
            timeout: Request timeout in seconds
        
        Returns:
            dict with success status and send count
        """
        try:
            payload = {
                "alertType": alert_type,
                "threatScore": threat_score,
                "cameraId": camera_id,
            }
            
            if message:
                payload["message"] = message
            if deep_link:
                payload["deepLink"] = deep_link
            if user_id:
                payload["userId"] = user_id
            
            response = requests.post(
                self.alert_endpoint,
                json=payload,
                timeout=timeout
            )
            
            result = response.json() if response.status_code == 200 else {}
            
            if response.status_code == 200:
                logger.info(f"Push notifications sent: {result.get('sent', 0)}/{result.get('total', 0)}")
                return {"success": True, **result}
            else:
                logger.error(f"Push notification failed: {response.status_code} - {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except requests.exceptions.Timeout:
            logger.error("Push notification request timed out")
            return {"success": False, "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to dashboard API at {self.api_url}")
            return {"success": False, "error": "Connection failed"}
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_notifier = None


def get_notifier(api_base_url: str = "http://localhost:3000") -> PushNotifier:
    """Get or create the push notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = PushNotifier(api_base_url)
    return _notifier


def notify_alert(
    alert_type: str,
    threat_score: float,
    camera_id: str = "unknown",
    message: Optional[str] = None,
    deep_link: Optional[str] = None,
    user_id: Optional[str] = None,
    api_base_url: str = "http://localhost:3000",
) -> dict:
    """
    Send a push notification for an alert
    
    Convenience function that uses the global notifier instance
    """
    notifier = get_notifier(api_base_url)
    return notifier.notify_alert(
        alert_type=alert_type,
        threat_score=threat_score,
        camera_id=camera_id,
        message=message,
        deep_link=deep_link,
        user_id=user_id,
    )
