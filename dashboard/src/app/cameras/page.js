"use client"

import Navbar from "../../../src/components/Navbar"
import { useState } from "react"

export default function AddCameraPage() {
  const [type, setType] = useState("rtsp")
  const [form, setForm] = useState({
    name: "",
    source: "",
    location: ""
  })
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit() {
    try {
      setLoading(true)
      const token = localStorage.getItem("visioniq_token")

      if (!token) {
        alert("Please login first")
        setLoading(false)
        return
      }

      const res = await fetch("/api/cameras", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ...form,
          type
        })
      })

      const data = await res.json()

      if (data.success) {
        alert("Camera connected 🚀")

        // reset form (nice UX)
        setForm({
          name: "",
          source: "",
          location: ""
        })

      } else {
        alert("Error: " + data.error)
      }

    } catch (err) {
      console.error(err)
      alert("Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#080c0e] text-white p-8">
      <Navbar />

      <div className="max-w-3xl mt-12 mx-auto">

        <h1 className="text-3xl text-green-400 font-semibold mb-2">Add Camera</h1>
        <p className="text-gray-400 mb-8">
          Connect a new video source to VisionIQ
        </p>

        {/* Camera Type */}
        <div className="grid grid-cols-3 gap-4 mb-8">

          {["rtsp", "webcam", "upload"].map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`p-4 rounded-xl border transition ${
                type === t
                  ? "border-green-400 bg-green-400/10"
                  : "border-white/10 hover:border-white/30"
              }`}
            >
              {t.toUpperCase()}
            </button>
          ))}

        </div>

        {/* Form */}
        <div className="space-y-4">

          <input
            name="name"
            value={form.name}
            placeholder="Camera Name"
            onChange={handleChange}
            className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
          />

          {type === "rtsp" && (
            <input
              name="source"
              value={form.source}
              placeholder="RTSP URL"
              onChange={handleChange}
              className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
            />
          )}

          {type === "upload" && (
            <input
              type="file"
              className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
            />
          )}

          <input
            name="location"
            value={form.location}
            placeholder="Location (optional)"
            onChange={handleChange}
            className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
          />

        </div>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-6 py-3 bg-white text-black rounded-lg disabled:opacity-50"
          >
            {loading ? "Connecting..." : "Connect Camera"}
          </button>

          <button className="px-6 py-3 border border-white/20 rounded-lg">
            Cancel
          </button>
        </div>

      </div>

    </main>
  )
}