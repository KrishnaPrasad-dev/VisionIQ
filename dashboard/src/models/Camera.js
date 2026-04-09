import mongoose from "mongoose"

const CameraRulesSchema = new mongoose.Schema(
  {
    restrictedZoneMonitoring: { type: Boolean, default: false },
    zoneLabel: { type: String, default: "" },
    maxPeopleAllowed: { type: Number, default: null },
    openHoursStart: { type: String, default: "" },
    openHoursEnd: { type: String, default: "" },
    notes: { type: String, default: "" },
  },
  { _id: false }
)

const CameraSchema = new mongoose.Schema({
  ownerId: { type: mongoose.Schema.Types.ObjectId, ref: "User", required: true, index: true },
  name: { type: String, required: true },
  source: { type: String, required: true },
  type: { type: String, required: true },
  location: { type: String },
  status: { type: String, default: "active" },
  rules: { type: CameraRulesSchema, default: () => ({}) },
  createdAt: { type: Date, default: Date.now }
})

export default mongoose.models.Camera || mongoose.model("Camera", CameraSchema)