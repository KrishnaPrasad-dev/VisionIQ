import { connectDB } from "../../../../lib/db";
import { getUserIdFromRequest } from "../../../../lib/auth";
import PushSubscription from "../../../../models/PushSubscription";

export async function POST(req) {
  try {
    const userId = getUserIdFromRequest(req);
    const body = await req.json();

    if (!body?.endpoint || !body?.keys?.auth || !body?.keys?.p256dh) {
      return Response.json(
        { success: false, error: "Invalid push subscription data" },
        { status: 400 }
      );
    }

    await connectDB();

    // Check if subscription already exists
    const existing = await PushSubscription.findOne({
      endpoint: body.endpoint,
    });

    if (existing) {
      return Response.json({
        success: true,
        message: "Subscription already registered",
      });
    }

    // Save new subscription
    const subscription = await PushSubscription.create({
      userId,
      endpoint: body.endpoint,
      auth: body.keys.auth,
      p256dh: body.keys.p256dh,
      userAgent: req.headers.get("user-agent"),
    });

    return Response.json({ success: true, subscription });
  } catch (err) {
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500;
    return Response.json(
      { success: false, error: err.message },
      { status }
    );
  }
}

export async function DELETE(req) {
  try {
    const userId = getUserIdFromRequest(req);
    const body = await req.json();

    if (!body?.endpoint) {
      return Response.json(
        { success: false, error: "Endpoint is required" },
        { status: 400 }
      );
    }

    await connectDB();

    await PushSubscription.deleteOne({
      userId,
      endpoint: body.endpoint,
    });

    return Response.json({ success: true, message: "Subscription removed" });
  } catch (err) {
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500;
    return Response.json(
      { success: false, error: err.message },
      { status }
    );
  }
}
