"use client"

import { useEffect, useRef, useState } from "react"

const WS_URL = "ws://localhost:8010/ws/stream"

export default function useVisionIQ() {

  const [data, setData] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const incoming = JSON.parse(e.data)
      setData(incoming)
    }

    ws.onclose = () => {
      console.log("AI stream disconnected")
    }

    return () => ws.close()

  }, [])

  return data
}