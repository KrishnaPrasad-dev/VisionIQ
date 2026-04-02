/**
 * Alert push trigger endpoint
 * Called when alerts are triggered to send push notifications to all subscribed users
 * Can be called from Python backend or other services
 */

import { connectDB } from "../../../../lib/db";
import PushSubscription from "../../../../models/PushSubscription";
import webpush from "web-push";

const publicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
const privateKey = process.env.VAPID_PRIVATE_KEY;
const ALERT_PUSH_COOLDOWN_MS = Number(process.env.PUSH_ALERT_COOLDOWN_MS || 90000);
const RECENT_ALERT_TTL_MS = Number(process.env.PUSH_ALERT_CACHE_TTL_MS || 10 * 60 * 1000);

const recentAlerts = globalThis.__visioniqRecentAlerts || new Map();
globalThis.__visioniqRecentAlerts = recentAlerts;

if (publicKey && privateKey) {
  webpush.setVapidDetails(
    process.env.VAPID_SUBJECT || "mailto:alerts@visioniq.com",
    publicKey,
    privateKey
  );
}

function buildAlertKey(body, threatLevel) {
  const cameraId = body.cameraId || "unknown";
  const roundedScore = Math.round(Number(body.threatScore || 0) / 10) * 10;
  return [cameraId, body.alertType || "alert", threatLevel, roundedScore].join("|");
}

function pruneRecentAlerts(now) {
  for (const [key, lastSeen] of recentAlerts.entries()) {
    if (now - lastSeen > RECENT_ALERT_TTL_MS) {
      recentAlerts.delete(key);
    }
  }
}

export async function POST(req) {
  try {
    const body = await req.json();

    // Validate required fields
    if (!body?.alertType || body?.threatScore === undefined) {
      return Response.json(
        { success: false, error: "alertType and threatScore are required" },
        { status: 400 }
      );
    }

    if (!privateKey || !publicKey) {
      return Response.json(
        { success: false, error: "VAPID keys not configured" },
        { status: 500 }
      );
    }

    await connectDB();

    // Get all subscriptions (or filter by userId if provided)
    const query = body.userId ? { userId: body.userId } : {};
    const subscriptions = await PushSubscription.find(query);

    if (subscriptions.length === 0) {
      return Response.json({
        success: true,
        sent: 0,
        message: "No active subscriptions",
      });
    }

    // Determine threat level based on score
    const threatLevel =
      body.threatScore >= 75
        ? "CRITICAL"
        : body.threatScore >= 45
          ? "SUSPICIOUS"
          : "INFO";

    const now = Date.now();
    pruneRecentAlerts(now);
    const alertKey = buildAlertKey(body, threatLevel);
    const lastSentAt = recentAlerts.get(alertKey) || 0;
    if (now - lastSentAt < ALERT_PUSH_COOLDOWN_MS) {
      return Response.json({
        success: true,
        sent: 0,
        failed: 0,
        total: 0,
        threatLevel,
        deduped: true,
        cooldownMs: ALERT_PUSH_COOLDOWN_MS,
      });
    }
    recentAlerts.set(alertKey, now);

    const notification = {
      title: `VisionIQ Alert - ${threatLevel}`,
      options: {
        body:
          body.message ||
          `${body.alertType} detected (Score: ${Math.round(body.threatScore)})`,
        icon: "/icon-192x192.png",
        badge: "/badge-72x72.png",
        tag: `alert-${body.cameraId || "unknown"}-${Date.now()}`,
        requireInteraction:
          body.threatScore >= 60 ? true : body.requireInteraction ?? false,
        data: {
          url: body.deepLink || "/dashboard",
          alertType: body.alertType,
          threatLevel,
          threatScore: body.threatScore,
          cameraId: body.cameraId,
          timestamp: now,
        },
      },
    };

    let sent = 0;
    let failed = 0;

    // Send to all subscriptions
    await Promise.all(
      subscriptions.map(async (sub) => {
        try {
          await webpush.sendNotification(
            {
              endpoint: sub.endpoint,
              keys: {
                auth: sub.auth,
                p256dh: sub.p256dh,
              },
            },
            JSON.stringify(notification)
          );
          sent++;
        } catch (err) {
          failed++;
          // Remove invalid subscriptions
          if (err.statusCode === 410 || err.statusCode === 404) {
            try {
              await PushSubscription.deleteOne({ _id: sub._id });
            } catch (delErr) {
              console.error("Failed to delete subscription:", delErr);
            }
          }
        }
      })
    );

    return Response.json({
      success: true,
      sent,
      failed,
      total: subscriptions.length,
      threatLevel,
    });
  } catch (err) {
    console.error("Alert push trigger error:", err);
    return Response.json(
      { success: false, error: err.message },
      { status: 500 }
    );
  }
}
