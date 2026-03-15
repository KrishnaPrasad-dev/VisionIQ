"use client"

import { useEffect, useState } from "react"

export default function AlertList() {

  const [alerts, setAlerts] = useState([])

  useEffect(() => {

    fetch("http://localhost:8000/alerts")
      .then(res => res.json())
      .then(data => setAlerts(data.alerts || []))

  }, [])

  return (

    <div className="grid md:grid-cols-3 gap-6">

      {alerts.map((alert, i) => (

        <div key={i} className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">

          {alert.snapshot_path && (
            <img src={`http://localhost:8000/${alert.snapshot_path}`} />
          )}

          <div className="p-4">

            <p className="text-xs text-gray-400">
              {alert.timestamp}
            </p>

            <p className="font-bold">
              {alert.status}
            </p>

            <p className="text-sm">
              Score: {alert.score}
            </p>

          </div>

        </div>

      ))}

    </div>

  )
}