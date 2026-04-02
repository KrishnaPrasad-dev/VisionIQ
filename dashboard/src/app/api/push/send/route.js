import { connectDB } from "../../../../lib/db";
import PushSubscription from "../../../../models/PushSubscription";
import webpush from "web-push";

// Configure web-push with VAPID keys
const publicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
const privateKey = process.env.VAPID_PRIVATE_KEY;

if (publicKey && privateKey) {
  webpush.setVapidDetails(
    process.env.VAPID_SUBJECT || "mailto:alerts@visioniq.com",
    publicKey,
    privateKey
  );
}

export async function POST(req) {
  try {
    const body = await req.json();

    if (!body?.title || !body?.options?.body) {
      return Response.json(
        { success: false, error: "Title and body are required" },
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

    const notification = {
      title: body.title,
      options: {
        body: body.options.body,
        icon: body.options.icon || "/icon-192x192.png",
        badge: body.options.badge || "/badge-72x72.png",
        tag: body.options.tag || "visioniq-alert",
        requireInteraction: body.options.requireInteraction ?? true,
        data: body.options.data || {},
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
          // If subscription is invalid, remove it
          if (err.statusCode === 410 || err.statusCode === 404) {
            try {
              await PushSubscription.deleteOne({ _id: sub._id });
            } catch (delErr) {
              console.error("Failed to delete subscription:", delErr);
            }
          } else {
            console.error("Push send error:", err.message);
          }
        }
      })
    );

    return Response.json({
      success: true,
      sent,
      failed,
      total: subscriptions.length,
    });
  } catch (err) {
    console.error("Push send error:", err);
    return Response.json(
      { success: false, error: err.message },
      { status: 500 }
    );
  }
}
