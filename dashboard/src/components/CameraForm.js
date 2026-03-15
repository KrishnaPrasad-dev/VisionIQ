"use client"

import { useState } from "react"

export default function CameraForm() {

  const [name, setName] = useState("")
  const [url, setUrl] = useState("")

  const addCamera = () => {

    console.log({
      name,
      url
    })

    alert("Camera Added!")

  }

  return (

    <div className="bg-white/5 border border-white/10 p-6 rounded-xl space-y-4">

      <input
        placeholder="Camera Name"
        className="w-full p-2 bg-black border border-white/10 rounded"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <input
        placeholder="RTSP / Camera URL"
        className="w-full p-2 bg-black border border-white/10 rounded"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />

      <button
        onClick={addCamera}
        className="w-full bg-green-500/20 border border-green-500 text-green-400 py-2 rounded"
      >
        Add Camera
      </button>

    </div>

  )
}