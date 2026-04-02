# Push Notifications Integration Guide

This document describes how to setup and use the browser push notification system for VisionIQ alerts.

## Quick Start

### 1. Generate VAPID Keys

VAPID keys are required for web push notifications. Generate them once and store securely:

```bash
cd dashboard
node -e "const webpush = require('web-push'); const vapidKeys = webpush.generateVAPIDKeys(); console.log('Public Key:\\n' + vapidKeys.publicKey); console.log('\\nPrivate Key:\\n' + vapidKeys.privateKey);"
```

### 2. Configure Environment Variables

Add to `.env.local` in the dashboard folder:

```env
NEXT_PUBLIC_VAPID_PUBLIC_KEY=<paste-public-key-here>
VAPID_PRIVATE_KEY=<paste-private-key-here>
VAPID_SUBJECT=mailto:your-email@example.com
MONGO_URI=<your-mongodb-connection-string>
JWT_SECRET=<your-jwt-secret>
```

### 3. API Endpoints

#### Subscribe to Push Notifications
- **POST** `/api/push/subscribe`
- Requires: `Authorization: Bearer <token>`
- Body:
```json
{
  "endpoint": "https://...",
  "keys": {
    "auth": "...",
    "p256dh": "..."
  }
}
```

#### Unsubscribe from Push Notifications
- **DELETE** `/api/push/subscribe`
- Requires: `Authorization: Bearer <token>`
- Body:
```json
{
  "endpoint": "https://..."
}
```

#### Send Push Notification
- **POST** `/api/push/send`
- Optional: `Authorization: Bearer <token>`
- Body:
```json
{
  "title": "Alert Title",
  "options": {
    "body": "Alert message",
    "icon": "/icon-192x192.png",
    "badge": "/badge-72x72.png",
    "tag": "alert-unique-id",
    "requireInteraction": true,
    "data": {
      "url": "/dashboard",
      "custom": "data"
    }
  },
  "userId": "optional-user-id-to-filter"
}
```

#### Trigger Alert Push Notification (Recommended for Alerts)
- **POST** `/api/push/alert`
- Body:
```json
{
  "alertType": "THREAT_DETECTED",
  "threatScore": 75,
  "cameraId": "cam_1",
  "message": "High threat activity detected",
  "deepLink": "/dashboard",
  "userId": "optional-user-id"
}
```
- Response:
```json
{
  "success": true,
  "sent": 5,
  "failed": 1,
  "total": 6,
  "threatLevel": "CRITICAL"
}
```

## Integration with Python Backend

To trigger push notifications from the Python AI engine when alerts are detected:

### Option 1: HTTP Call from Python Backend

In your `stream_server.py` or alert emission code, add:

```python
import requests

def emit_alert(alert_type, threat_score, camera_id, message=None):
    """Emit alert via WebSocket and push notification"""
    
    # Existing WebSocket emit code
    # await websocket_manager.broadcast({...})
    
    # NEW: Send push notification
    try:
        response = requests.post(
            "http://localhost:3000/api/push/alert",
            json={
                "alertType": alert_type,
                "threatScore": threat_score,
                "cameraId": camera_id,
                "message": message or f"{alert_type} detected"
            },
            timeout=3
        )
        if response.status_code == 200:
            result = response.json()
            print(f"Push notifications sent: {result['sent']}/{result['total']}")
        else:
            print(f"Push notification failed: {response.status_code}")
    except Exception as e:
        print(f"Error sending push notification: {e}")
```

### Option 2: Database Trigger

Set up a trigger in MongoDB that notifies the dashboard when alerts are created.

## Frontend Usage

### Automatic On Dashboard Load

Push notifications are automatically enabled when users visit the dashboard:
1. Service worker is registered (`/public/sw.js`)
2. Browser permission is requested
3. Subscription is saved to MongoDB via `/api/push/subscribe`

### Manual Permission Request

To manually request notification permission in any component:

```javascript
import usePushNotifications from "@/hooks/usePushNotifications"

export function MyComponent() {
  const { requestNotificationPermission } = usePushNotifications()
  
  return (
    <button onClick={requestNotificationPermission}>
      Enable Notifications
    </button>
  )
}
```

### Send Notification from Frontend

Import and use the push utilities:

```javascript
import { sendAlertNotification } from "@/lib/pushNotifications"

// Send an alert notification
await sendAlertNotification({
  alertType: "THREAT_DETECTED",
  threatLevel: "CRITICAL",
  threatScore: 85,
  cameraId: "cam_1",
  message: "Suspicious activity detected in entrance",
  token: localStorage.getItem("authToken")
})
```

## Service Worker

The service worker (`/public/sw.js`) handles:
- Push notification display
- Notification clicks (opens dashboard)
- Notification dismissal
- Automatic browser handling

## Database Schema

### PushSubscription

```javascript
{
  _id: ObjectId,
  userId: ObjectId,          // Reference to User
  endpoint: String,          // Push service endpoint (unique)
  auth: String,              // Authentication key
  p256dh: String,            // Encryption key
  userAgent: String,         // Browser info
  createdAt: Date,
  updatedAt: Date
}
```

## Troubleshooting

### Notifications not appearing?

1. Check browser permissions: Visit notification settings
2. Check MongoDB connection: Verify `MONGO_URI` is correct
3. Check VAPID keys: Ensure keys are properly configured
4. Check service worker: Open DevTools > Application > Service Workers
5. Check subscriptions: Query MongoDB: `db.pushsubscriptions.find()`

### "VAPID keys not configured" error

1. Generate VAPID keys (see step 1 above)
2. Add to `.env.local`
3. Restart the Next.js development server

### Subscriptions appearing but no push received

1. Check `/api/push/send` response for failures
2. Invalid subscriptions are automatically cleaned up
3. Check browser console for errors
4. Verify email in `VAPID_SUBJECT` is valid

## Testing

### Test Push Notification Locally

```bash
# In dashboard directory
curl -X POST http://localhost:3000/api/push/alert \
  -H "Content-Type: application/json" \
  -d '{
    "alertType": "TEST",
    "threatScore": 50,
    "cameraId": "test",
    "message": "Test notification"
  }'
```

### Monitor in Browser

Open DevTools and check:
- Console: for any JavaScript errors
- Network: requests to `/api/push/subscribe` and `/api/push/send`
- Application > Service Workers: registration status
- Application > Manifest: push subscription keys

## Notes

- Push subscriptions are browser-specific; the same user will have different subscriptions on different devices
- Invalid subscriptions (410/404 errors) are automatically removed
- Notifications with `requireInteraction: true` will require user action to dismiss
- The bell icon in the navbar shows a notification badge
