"use client"

import { useEffect, useRef, useState } from "react"

const WS_URL = "ws://localhost:8000/ws/stream"

export default function LiveFeed() {

  const [frame, setFrame] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      setFrame("data:image/jpeg;base64," + data.annotated_base64)
    }

    return () => ws.close()

  }, [])

  return (

    <div className="bg-black rounded-xl border border-white/10 overflow-hidden aspect-video">

      {frame ? (
        <img src={frame} className="w-full h-full object-cover" />
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500">
          Waiting for camera feed...
        </div>
      )}

    </div>

  )
}