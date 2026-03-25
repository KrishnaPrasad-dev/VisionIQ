"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Navbar from "../../../src/components/Navbar"
import GridBackground from "../../../src/components/GridBackground"

const TYPES = ["rtsp", "ipcam", "webcam", "upload"]

export default function CamerasPage() {
  const [type, setType] = useState("rtsp")
  const [form, setForm] = useState({
    name: "",
    source: "",
    location: ""
  })
  const [loadingSave, setLoadingSave] = useState(false)
  const [loadingTest, setLoadingTest] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [cameras, setCameras] = useState([])
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState("all")
  const [phoneIp, setPhoneIp] = useState("")
  const [selectedFile, setSelectedFile] = useState(null)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  function normalizeSource(rawSource, currentType) {
    let source = String(rawSource || "").trim()

    if (currentType === "webcam" && !source) {
      return "0"
    }

    if (currentType === "ipcam") {
      // Most phone camera apps expose plain HTTP streams, not HTTPS.
      source = source.replace(/^https:\/\//i, "http://")

      // If user enters just ip:port endpoint, assume common MJPEG suffix.
      if (/^http:\/\/(\d{1,3}\.){3}\d{1,3}(:\d+)?\/?$/i.test(source)) {
        source = source.replace(/\/?$/, "/video")
      }
    }

    return source
  }

  async function uploadVideoAndGetSource() {
    if (!selectedFile) {
      throw new Error("Select a video file first")
    }

    const fd = new FormData()
    fd.append("file", selectedFile)

    const res = await fetch("/api/cameras/upload", {
      method: "POST",
      body: fd
    })

    const data = await res.json()
    if (!data.success || !data.source) {
      throw new Error(data.error || "Upload failed")
    }

    return data.source
  }

  async function resolveSourceForActions() {
    if (type === "upload") {
      return uploadVideoAndGetSource()
    }
    return normalizeSource(form.source, type)
  }

  const token = typeof window !== "undefined" ? localStorage.getItem("visioniq_token") : null

  const fetchCameras = useCallback(async () => {
    if (!token) {
      setListLoading(false)
      return
    }

    try {
      setListLoading(true)
      const res = await fetch("/api/cameras", {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })
      const data = await res.json()
      if (data.success) {
        setCameras(data.cameras || [])
      }
    } finally {
      setListLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetchCameras()
  }, [fetchCameras])

  async function handleSubmit() {
    try {
      setLoadingSave(true)

      if (!token) {
        alert("Please login first")
        setLoadingSave(false)
        return
      }

      const resolvedSource = await resolveSourceForActions()

      const res = await fetch("/api/cameras", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ...form,
          source: resolvedSource,
          type
        })
      })

      const data = await res.json()

      if (data.success) {
        alert("Camera connected")

        setForm({
          name: "",
          source: "",
          location: ""
        })
        setSelectedFile(null)

        await fetchCameras()

      } else {
        alert("Error: " + data.error)
      }

    } catch (err) {
      console.error(err)
      alert("Something went wrong")
    } finally {
      setLoadingSave(false)
    }
  }

  async function handleTestSource() {
    const resolvedSource = await resolveSourceForActions()

    if (!resolvedSource) {
      alert("Add a source URL first")
      return
    }
    if (!token) {
      alert("Please login first")
      return
    }

    try {
      setLoadingTest(true)
      const res = await fetch("/api/cameras", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ testOnly: true, source: resolvedSource })
      })

      const data = await res.json()
      if (data.success) {
        alert("Connection test passed")
      } else {
        alert("Connection test failed: " + data.error)
      }
    } finally {
      setLoadingTest(false)
    }
  }

  async function toggleStatus(camera) {
    if (!token) return

    const nextStatus = camera.status === "active" ? "inactive" : "active"
    const res = await fetch("/api/cameras", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ id: camera._id, status: nextStatus })
    })

    const data = await res.json()
    if (data.success) {
      setCameras(prev => prev.map(c => c._id === camera._id ? { ...c, status: nextStatus } : c))
    } else {
      alert(data.error || "Failed to update camera")
    }
  }

  async function removeCamera(cameraId) {
    if (!token) return
    const confirmed = confirm("Delete this camera?")
    if (!confirmed) return

    const res = await fetch(`/api/cameras?id=${cameraId}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })

    const data = await res.json()
    if (data.success) {
      setCameras(prev => prev.filter(c => c._id !== cameraId))
    } else {
      alert(data.error || "Delete failed")
    }
  }

  const filtered = useMemo(() => {
    return cameras.filter(camera => {
      const matchesType = typeFilter === "all" ? true : camera.type === typeFilter
      const q = search.trim().toLowerCase()
      const matchesSearch = !q
        ? true
        : (camera.name || "").toLowerCase().includes(q)
          || (camera.location || "").toLowerCase().includes(q)
          || (camera.source || "").toLowerCase().includes(q)

      return matchesType && matchesSearch
    })
  }, [cameras, typeFilter, search])

  function applyIpCamPreset(kind) {
    const ip = phoneIp.trim()
    if (!ip) {
      alert("Enter your phone IP first (e.g. 192.168.1.10)")
      return
    }

    const source =
      kind === "ipwebcam-http"
        ? `http://${ip}:8080/video`
        : kind === "droidcam-http"
        ? `http://${ip}:4747/video`
        : `rtsp://${ip}:8554/unicast`

    setForm(prev => ({ ...prev, source }))
  }

  return (
    <main className="min-h-screen bg-[#080c0e] text-white">
      <GridBackground />
      <Navbar />

      <div className="max-w-7xl mt-8 mx-auto px-4 sm:px-6 pt-20 pb-14">

        <div className="mb-8 rounded-2xl border border-white/10 bg-black/30 backdrop-blur px-5 py-5 sm:px-6 sm:py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] tracking-[0.18em] text-green-300/80 mb-2">SOURCE CONTROL</p>
              <h1 className="text-3xl sm:text-4xl text-white font-semibold mb-2">Camera Manager</h1>
              <p className="text-gray-400 text-sm sm:text-base">Manage sources, validate streams, and control active cameras.</p>
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <span className="px-2.5 py-1 text-xs rounded-full border border-green-500/40 bg-green-500/10 text-green-300">
                {cameras.length} Total
              </span>
              <span className="px-2.5 py-1 text-xs rounded-full border border-white/20 text-gray-300">
                {filtered.length} Visible
              </span>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-[1fr_380px] gap-6">

          <section className="rounded-2xl border border-white/10 bg-black/35 backdrop-blur p-4 md:p-5 shadow-[0_10px_40px_rgba(0,0,0,0.35)]">

            <div className="flex flex-col md:flex-row gap-3 md:items-center md:justify-between mb-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  placeholder="Search name, location, source"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full md:w-80 p-2.5 bg-black/50 border border-white/10 rounded-xl text-sm outline-none focus:border-green-400/60"
                />

                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="p-2.5 pr-3 bg-black/50 border border-white/10 rounded-xl text-sm outline-none focus:border-green-400/60"
                >
                  <option value="all">All types</option>
                  {TYPES.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                </select>
              </div>

              <button
                onClick={fetchCameras}
                className="px-4 py-2 border border-white/20 rounded-xl text-sm hover:bg-white/5 transition"
              >
                Refresh
              </button>
            </div>

            {listLoading ? (
              <div className="text-gray-400 text-sm p-6">Loading cameras...</div>
            ) : filtered.length === 0 ? (
              <div className="text-gray-500 text-sm p-6">No cameras found</div>
            ) : (
              <div className="space-y-3">
                {filtered.map(camera => {
                  const isActive = camera.status !== "inactive"
                  return (
                    <div key={camera._id} className="rounded-xl border border-white/10 bg-gradient-to-b from-white/[0.06] to-white/[0.02] p-4 hover:border-green-400/35 transition">
                      <div className="flex flex-wrap gap-3 items-center justify-between">
                        <div className="min-w-[220px]">
                          <div className="flex items-center gap-2">
                            <div className="font-semibold text-white">{camera.name}</div>
                            <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/20 text-gray-300">{camera.type?.toUpperCase()}</span>
                          </div>
                          <div className="text-xs text-gray-400 mt-1">{camera.location || "No location"}</div>
                          <div className="text-xs text-gray-500 mt-1 break-all">{camera.source}</div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded border ${isActive ? "border-green-500/50 text-green-400 bg-green-500/10" : "border-gray-500/40 text-gray-300 bg-gray-500/10"}`}>
                            {isActive ? "ACTIVE" : "INACTIVE"}
                          </span>

                          <button
                            onClick={() => toggleStatus(camera)}
                            className="text-xs px-2 py-1 rounded-lg border border-white/20 hover:bg-white/5 transition"
                          >
                            {isActive ? "Pause" : "Activate"}
                          </button>

                          <button
                            onClick={() => removeCamera(camera._id)}
                            className="text-xs px-2 py-1 rounded-lg border border-red-500/40 text-red-300 hover:bg-red-500/10 transition"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

          </section>

          <section className="rounded-2xl border border-white/10 bg-black/35 backdrop-blur p-5 h-fit lg:sticky lg:top-24 shadow-[0_10px_40px_rgba(0,0,0,0.35)]">

            <h2 className="text-xl text-green-400 font-semibold mb-1">Add Camera</h2>
            <p className="text-gray-400 mb-6 text-sm">Connect a new video source to VisionIQ</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-5">

              {TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setType(t)}
                  className={`p-2.5 rounded-xl border text-sm transition ${
                    type === t
                      ? "border-green-400 bg-green-400/10"
                      : "border-white/10 hover:border-white/30 hover:bg-white/5"
                  }`}
                >
                  {t.toUpperCase()}
                </button>
              ))}

            </div>

            <div className="space-y-3">

              <input
                name="name"
                value={form.name}
                placeholder="Camera Name"
                onChange={handleChange}
                className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
              />

              {type !== "upload" && (
                <input
                  name="source"
                  value={form.source}
                  placeholder={
                    type === "rtsp"
                      ? "RTSP URL"
                      : type === "ipcam"
                      ? "IP Cam URL (http://... or rtsp://...)"
                      : "Camera Source"
                  }
                  onChange={handleChange}
                  className="w-full p-3 bg-black/50 border border-white/10 rounded-xl outline-none focus:border-green-400/60"
                />
              )}

              {type === "ipcam" && (
                <div className="rounded-lg border border-white/10 bg-black/25 p-3 space-y-2">
                  <p className="text-xs text-gray-400">
                    Phone IP camera quick fill
                  </p>
                  <input
                    value={phoneIp}
                    onChange={(e) => setPhoneIp(e.target.value)}
                    placeholder="Phone IP (e.g. 192.168.1.10)"
                    className="w-full p-2.5 bg-black/50 border border-white/10 rounded-xl text-sm outline-none focus:border-green-400/60"
                  />
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => applyIpCamPreset("ipwebcam-http")}
                      className="px-2 py-1 text-xs rounded-lg border border-white/20 hover:bg-white/5 transition"
                    >
                      IP Webcam (HTTP)
                    </button>
                    <button
                      type="button"
                      onClick={() => applyIpCamPreset("droidcam-http")}
                      className="px-2 py-1 text-xs rounded-lg border border-white/20 hover:bg-white/5 transition"
                    >
                      DroidCam (HTTP)
                    </button>
                    <button
                      type="button"
                      onClick={() => applyIpCamPreset("ipwebcam-rtsp")}
                      className="px-2 py-1 text-xs rounded-lg border border-white/20 hover:bg-white/5 transition"
                    >
                      Generic RTSP
                    </button>
                  </div>
                </div>
              )}

              {type === "upload" && (
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full p-3 bg-black/40 border border-white/10 rounded-lg"
                />
              )}

              {type === "upload" && selectedFile && (
                <div className="text-xs text-gray-400">Selected: {selectedFile.name}</div>
              )}

              <input
                name="location"
                value={form.location}
                placeholder="Location (optional)"
                onChange={handleChange}
                className="w-full p-3 bg-black/50 border border-white/10 rounded-xl outline-none focus:border-green-400/60"
              />

            </div>

            <div className="mt-6 flex gap-2">
              <button
                onClick={handleTestSource}
                disabled={loadingTest}
                className="px-4 py-2 border border-white/20 rounded-xl text-sm disabled:opacity-50 hover:bg-white/5 transition"
              >
                {loadingTest ? "Testing..." : "Test Connection"}
              </button>

              <button
                onClick={handleSubmit}
                disabled={loadingSave}
                className="px-4 py-2 bg-green-400 text-black rounded-xl text-sm font-medium disabled:opacity-50 hover:bg-green-300 transition"
              >
                {loadingSave ? "Connecting..." : "Connect Camera"}
              </button>
            </div>

          </section>

        </div>

      </div>

    </main>
  )
}