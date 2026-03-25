import fs from "fs"
import path from "path"

function sanitizeFileName(name) {
  return String(name || "video.mp4").replace(/[^a-zA-Z0-9._-]/g, "_")
}

export async function POST(req) {
  try {
    const formData = await req.formData()
    const file = formData.get("file")

    if (!file || typeof file === "string") {
      return Response.json({ success: false, error: "File is required" }, { status: 400 })
    }

    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    // dashboard/ -> ../ai-engine/test_videos/uploads
    const uploadDir = path.resolve(process.cwd(), "../ai-engine/test_videos/uploads")
    fs.mkdirSync(uploadDir, { recursive: true })

    const safe = sanitizeFileName(file.name)
    const targetName = `${Date.now()}_${safe}`
    const targetPath = path.join(uploadDir, targetName)

    fs.writeFileSync(targetPath, buffer)

    // Return POSIX-like slashes for consistency in UI and backend use.
    const source = targetPath.replace(/\\/g, "/")

    return Response.json({ success: true, source })
  } catch (err) {
    return Response.json({ success: false, error: err?.message || "Upload failed" }, { status: 500 })
  }
}
