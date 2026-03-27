import { connectDB } from "../../../lib/db"
import { getUserIdFromRequest } from "../../../lib/auth"
import Camera from "../../../models/Camera"

const ENGINE_BASE = process.env.QUANTUMEYE_ENGINE_URL || "http://localhost:8010"

async function notifyEngineStart(cameraId, source) {
  await fetch(`${ENGINE_BASE}/start-camera`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      id: cameraId,
      source
    })
  })
}

async function testEngineSource(source) {
  const res = await fetch(`${ENGINE_BASE}/test-source`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ source })
  })

  let payload = null
  try {
    payload = await res.json()
  } catch {
    payload = null
  }

  if (!res.ok) {
    const detail = payload?.detail
    throw new Error(detail?.message || payload?.message || "Connection test failed")
  }

  return payload
}

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

    if (body?.testOnly) {
      if (!body?.source) {
        return Response.json({ success: false, error: "Source is required" }, { status: 400 })
      }

      try {
        await testEngineSource(body.source)
        return Response.json({ success: true, message: "Source reachable" })
      } catch (engineErr) {
        return Response.json({ success: false, error: engineErr?.message || "Connection test failed" }, { status: 502 })
      }
    }

    await connectDB()

    if (!body?.name || !body?.source || !body?.type) {
      return Response.json({ success: false, error: "name, source and type are required" }, { status: 400 })
    }

    const camera = await Camera.create({
      ownerId: userId,
      name: body.name,
      source: body.source,
      type: body.type,
      location: body.location
    })

    // Notify AI stream service to start this camera source
    try {
      await notifyEngineStart(camera._id, camera.source)
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

export async function PATCH(req) {
  try {
    const userId = getUserIdFromRequest(req)
    const body = await req.json()

    if (!body?.id) {
      return Response.json({ success: false, error: "Camera id is required" }, { status: 400 })
    }

    await connectDB()

    const camera = await Camera.findOneAndUpdate(
      { _id: body.id, ownerId: userId },
      {
        $set: {
          ...(body.name !== undefined ? { name: body.name } : {}),
          ...(body.location !== undefined ? { location: body.location } : {}),
          ...(body.status !== undefined ? { status: body.status } : {})
        }
      },
      { new: true }
    )

    if (!camera) {
      return Response.json({ success: false, error: "Camera not found" }, { status: 404 })
    }

    return Response.json({ success: true, camera })
  } catch (err) {
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500
    return Response.json({ success: false, error: err.message }, { status })
  }
}

export async function DELETE(req) {
  try {
    const userId = getUserIdFromRequest(req)
    const { searchParams } = new URL(req.url)
    const id = searchParams.get("id")

    if (!id) {
      return Response.json({ success: false, error: "Camera id is required" }, { status: 400 })
    }

    await connectDB()

    const deleted = await Camera.findOneAndDelete({ _id: id, ownerId: userId })

    if (!deleted) {
      return Response.json({ success: false, error: "Camera not found" }, { status: 404 })
    }

    return Response.json({ success: true })
  } catch (err) {
    const status = err.message?.includes("token") || err.message?.includes("auth") ? 401 : 500
    return Response.json({ success: false, error: err.message }, { status })
  }
}