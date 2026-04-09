const AI_ENGINE_BASE = process.env.VISIONIQ_ENGINE_URL || process.env.QUANTUMEYE_ENGINE_URL || "http://localhost:8010"

export async function POST(req) {
  try {
    const body = await req.json()
    const cameraId = String(body?.camera_id || "").trim()

    if (!cameraId) {
      return Response.json({ success: false, error: "camera_id is required" }, { status: 400 })
    }

    const res = await fetch(`${AI_ENGINE_BASE}/ack-alert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ camera_id: cameraId }),
    })

    const payload = await res.json().catch(() => ({}))
    if (!res.ok || payload?.success === false) {
      return Response.json({ success: false, error: payload?.error || "Ack failed" }, { status: 502 })
    }

    return Response.json({ success: true })
  } catch (err) {
    return Response.json({ success: false, error: err?.message || "Ack failed" }, { status: 500 })
  }
}