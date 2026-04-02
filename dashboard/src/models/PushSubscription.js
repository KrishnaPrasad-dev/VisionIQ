import mongoose from "mongoose";

const pushSubscriptionSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },
    endpoint: {
      type: String,
      required: true,
      unique: true,
    },
    auth: {
      type: String,
      required: true,
    },
    p256dh: {
      type: String,
      required: true,
    },
    userAgent: {
      type: String,
      default: null,
    },
  },
  { timestamps: true }
);

export default mongoose.models.PushSubscription ||
  mongoose.model("PushSubscription", pushSubscriptionSchema);
