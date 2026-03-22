import mongoose from "mongoose"

const CameraSchema = new mongoose.Schema({
  ownerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true, index: true },
  name: { type: String, required: true },
  source: { type: String, required: true },
  type: { type: String, required: true },
  location: { type: String },
  status: { type: String, default: "active" },
  createdAt: { type: Date, default: Date.now }
})

export default mongoose.models.Camera || mongoose.model("Camera", CameraSchema)