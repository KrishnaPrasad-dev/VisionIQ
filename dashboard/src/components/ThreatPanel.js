"use client"

import { useState } from "react"

export default function ThreatPanel() {

  const [score, setScore] = useState(0)

  const overrideSafe = async () => {

    await fetch("http://localhost:8000/override_safe", {
      method: "POST"
    })

    setScore(0)

  }

  return (

    <div className="bg-white/5 border border-white/10 p-5 rounded-xl">

      <p className="text-xs text-gray-400 mb-3 tracking-widest">
        THREAT SCORE
      </p>

      <h1 className="text-4xl font-bold mb-4">
        {score}
      </h1>

      <button
        onClick={overrideSafe}
        className="w-full bg-red-500/20 border border-red-500 text-red-400 py-2 rounded-lg"
      >
        Override Safe
      </button>

    </div>

  )
}