/**
 * Utility to send push notifications
 * Can be called from API routes or scheduled tasks
 */

const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

export async function sendPushNotification({
  title,
  body,
  icon,
  badge,
  tag,
  requireInteraction = true,
  data = {},
  userId = null,
  token = null,
}) {
  try {
    const response = await fetch(`${baseUrl}/api/push/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify({
        title,
        userId,
        options: {
          body,
          icon: icon || "/icon-192x192.png",
          badge: badge || "/badge-72x72.png",
          tag: tag || "visioniq-alert",
          requireInteraction,
          data,
        },
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      console.error("Failed to send push notification:", result.error);
      return {
        success: false,
        error: result.error,
      };
    }

    return result;
  } catch (error) {
    console.error("Error sending push notification:", error);
    return {
      success: false,
      error: error.message,
    };
  }
}

export async function sendAlertNotification({
  alertType,
  threatLevel,
  threatScore,
  cameraId,
  message,
  userId = null,
  token = null,
}) {
  const title = `VisionIQ Alert - ${threatLevel}`;
  const body = message || `Threat detected: ${alertType} (Score: ${threatScore})`;
  const tag = `alert-${cameraId}-${Date.now()}`;

  return sendPushNotification({
    title,
    body,
    tag,
    data: {
      url: "/dashboard",
      alertType,
      threatLevel,
      threatScore,
      cameraId,
    },
    userId,
    token,
  });
}
