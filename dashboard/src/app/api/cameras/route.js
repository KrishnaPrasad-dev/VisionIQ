import { connectDB } from "@/lib/db"
import { getUserIdFromRequest } from "@/lib/auth"
import Camera from "@/models/Camera"

export async function GET(req) {
  try {
    const userId = getUserIdFromRequest(req)
    await connectDB()

    const cameras = await Camera.find({ ownerId: userId })
      .sort({ createdAt: -1 })
      .lean()

    return Response.json({ success: true, cameras })

  } catch (err) {
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500
    return Response.json({ success: false, error: err.message }, { status })
  }
}

export async function POST(req) {
  try {
    const userId = getUserIdFromRequest(req)
    const body = await req.json()

    await connectDB()

    const camera = await Camera.create({
      ownerId: userId,
      name: body.name,
      source: body.source,
      type: body.type,
      location: body.location
    })

    // 🔥 Notify AI Engine
    try {
      await fetch("http://localhost:5000/start-camera", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          id: camera._id,
          source: camera.source
        })
      })
    } catch (engineErr) {
      console.warn("AI engine notify failed:", engineErr?.message || engineErr)
    }

    return Response.json({ success: true, camera })

  } catch (err) {
    console.error(err)
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500
    return Response.json({ success: false, error: err.message }, { status })
  }
}