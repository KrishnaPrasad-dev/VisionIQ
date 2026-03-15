"use client"

import Navbar from "../../components/Navbar"
import GridBackground from "../../components/GridBackground"
import useVisionIQ from "../../hooks/useVisionIQ"

export default function DashboardPage(){

  const data = useVisionIQ()

  const score = data?.threat_score ?? 0

  const status =
    score >= 75 ? "CRITICAL"
    : score >= 45 ? "SUSPICIOUS"
    : "SAFE"

  const statusColor =
    status === "CRITICAL"
      ? "#ef4444"
      : status === "SUSPICIOUS"
      ? "#f59e0b"
      : "#22c55e"

  return(

    <main className="min-h-screen mb-24 bg-[#080c0e] text-white">

      <GridBackground/>
      <Navbar/>

      <div className="max-w-7xl mx-auto pt-32 px-6">

        {/* HEADER */}
        <div className="flex justify-between items-center mb-10">

          <div>
            <h1 className="text-xl font-bold tracking-wider">
              LIVE MONITORING
            </h1>

            <p className="text-gray-500 text-sm">
              VisionIQ AI Surveillance
            </p>
          </div>

          <StatusBadge status={status}/>
        </div>

        <div className="grid md:grid-cols-[1fr_340px] gap-6">

          {/* CAMERA FEED */}
          <CameraFeed frame={data?.annotated_base64}/>

          {/* RIGHT PANEL */}
          <div className="space-y-5">

            <ThreatMeter score={score}/>

            <Metrics metrics={data}/>

          </div>

        </div>

      </div>

    </main>

  )
}

function CameraFeed({frame}){

  return(

    <div className="relative bg-black rounded-xl border border-white/10 overflow-hidden aspect-video">

      {frame ? (
        <img
          src={"data:image/jpeg;base64," + frame}
          className="w-full h-full object-cover"
        />
      ):(
        <div className="flex items-center justify-center h-full text-gray-500">
          Waiting for feed...
        </div>
      )}

      {/* corner brackets */}
      <div className="absolute top-2 left-2 w-6 h-6 border-t-2 border-l-2 border-green-400"/>
      <div className="absolute top-2 right-2 w-6 h-6 border-t-2 border-r-2 border-green-400"/>
      <div className="absolute bottom-2 left-2 w-6 h-6 border-b-2 border-l-2 border-green-400"/>
      <div className="absolute bottom-2 right-2 w-6 h-6 border-b-2 border-r-2 border-green-400"/>

    </div>

  )
}

function ThreatMeter({score}){

  const pct = Math.min(100, Math.max(0, score))

  const color =
    pct >= 70 ? "#ef4444"
    : pct >= 40 ? "#f59e0b"
    : "#22c55e"

  return(

    <div className="bg-white/5 border border-white/10 rounded-xl p-5">

      <div className="flex justify-between mb-3">

        <span className="text-xs text-gray-400 tracking-widest">
          THREAT SCORE
        </span>

        <span
          className="text-3xl font-bold"
          style={{color}}
        >
          {Math.round(pct)}
        </span>

      </div>

      <div className="h-2 bg-white/10 rounded-full overflow-hidden">

        <div
          style={{
            width: pct + "%",
            background: color
          }}
          className="h-full transition-all duration-300"
        />

      </div>

    </div>

  )
}

function Metrics({metrics}){

  return(

    <div className="grid grid-cols-2 gap-4">

      <Metric title="People" value={metrics?.person_count ?? 0}/>
      <Metric title="Loitering" value={metrics?.loitering_count ?? 0}/>
      <Metric title="Zone Breach" value={metrics?.zone_triggered ? "YES":"NO"}/>
      <Metric title="After Hours" value={metrics?.after_hours ? "YES":"NO"}/>

    </div>

  )
}

function Metric({title,value}){

  return(

    <div className="bg-white/5 border border-white/10 rounded-xl p-4">

      <p className="text-xs text-gray-400 mb-1">
        {title}
      </p>

      <h2 className="text-xl font-bold">
        {value}
      </h2>

    </div>

  )
}

function StatusBadge({status}){

  const color =
    status === "CRITICAL"
      ? "#ef4444"
      : status === "SUSPICIOUS"
      ? "#f59e0b"
      : "#22c55e"

  return(

    <div
      className="px-4 py-2 rounded-lg border text-sm font-semibold"
      style={{
        color,
        borderColor: color,
        background: color + "20"
      }}
    >
      {status}
    </div>

  )
}