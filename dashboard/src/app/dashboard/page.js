"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import Navbar from "../../components/Navbar"
import GridBackground from "../../components/GridBackground"
import useVisionIQ from "../../hooks/useVisionIQ"
import usePushNotifications from "../../hooks/usePushNotifications"

export default function DashboardPage(){

  const ALERT_COOLDOWN_MS = 15000

  const data = useVisionIQ()
  usePushNotifications()

  const [events, setEvents] = useState([])
  const [dismissed, setDismissed] = useState([])
  const [acknowledged, setAcknowledged] = useState([])
  const [nowMs, setNowMs] = useState(Date.now())
  const lastAlertRef = useRef({
    at: 0,
    status: "SAFE",
    score: 0,
    fingerprint: "",
  })

  const score = data?.threat_score ?? 0

  const status =
    score >= 75 ? "CRITICAL"
    : score >= 45 ? "SUSPICIOUS"
    : "SAFE"

  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!data) return

    const id = `${data?.ts ?? Date.now()}-${Math.round(data?.threat_score ?? 0)}-${data?.person_count ?? 0}`
    const item = {
      id,
      ts: data?.ts ? Number(data.ts) * 1000 : Date.now(),
      score: Math.round(data?.threat_score ?? 0),
      status: (data?.threat_score ?? 0) >= 75
        ? "CRITICAL"
        : (data?.threat_score ?? 0) >= 45
        ? "SUSPICIOUS"
        : "SAFE",
      personCount: data?.person_count ?? 0,
      zoneTriggered: Boolean(data?.zone_triggered),
      afterHours: Boolean(data?.after_hours),
      message:
        (data?.threat_score ?? 0) >= 75
          ? "High threat activity detected"
          : (data?.threat_score ?? 0) >= 45
          ? "Suspicious pattern detected"
          : "Baseline monitoring"
    }

    if (item.status === "SAFE") {
      return
    }

    const fingerprint = `${item.status}-${item.personCount}-${item.zoneTriggered}-${item.afterHours}`
    const gate = lastAlertRef.current
    const cooldownPassed = item.ts - gate.at >= ALERT_COOLDOWN_MS
    const escalatedToCritical = gate.status !== "CRITICAL" && item.status === "CRITICAL"
    const majorScoreShift = Math.abs(item.score - gate.score) >= 20
    const changedPattern = gate.fingerprint !== fingerprint

    if (!cooldownPassed && !escalatedToCritical && !majorScoreShift && !changedPattern) {
      return
    }

    lastAlertRef.current = {
      at: item.ts,
      status: item.status,
      score: item.score,
      fingerprint,
    }

    setEvents(prev => {
      if (prev[0]?.id === item.id) return prev
      return [item, ...prev].slice(0, 40)
    })
  }, [data])

  const activeAlerts = useMemo(
    () => events.filter(e => e.status !== "SAFE" && !dismissed.includes(e.id)).slice(0, 6),
    [events, dismissed]
  )

  const lastSeenAgeMs = nowMs - (data?.ts ? Number(data.ts) * 1000 : 0)
  const streamOnline = Boolean(data?.ts) && lastSeenAgeMs < 6000

  return(

    <main className="min-h-screen mb-24 bg-[#080c0e] text-white">

      <GridBackground/>
      <Navbar/>

      <div className="max-w-7xl mx-auto pt-20 px-6">

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
          <CameraFeed frame={data?.annotated_base64} state={data?.status} message={data?.message}/>

          {/* RIGHT PANEL */}
          <div className="space-y-5">

            <ThreatMeter score={score}/>

            <Metrics metrics={data}/>

            <CameraHealthPanel
              streamOnline={streamOnline}
              lastSeenAgeMs={lastSeenAgeMs}
              fps={data?.fps}
              latency={data?.latency_ms}
            />

          </div>

        </div>

        <IncidentTimeline events={events}/>

      </div>

      <AlertRail
        alerts={activeAlerts}
        acknowledged={acknowledged}
        onAcknowledge={(id) => setAcknowledged(prev => prev.includes(id) ? prev : [id, ...prev])}
        onDismiss={(id) => setDismissed(prev => prev.includes(id) ? prev : [id, ...prev])}
      />

    </main>

  )
}

function CameraFeed({frame, state, message}){

  return(

    <div className="relative bg-black rounded-xl border border-white/10 overflow-hidden aspect-video">

      {frame ? (
        <img
          src={"data:image/jpeg;base64," + frame}
          className="w-full h-full object-cover"
        />
      ):(
        <div className="flex flex-col items-center justify-center h-full text-gray-500 px-6 text-center">
          <div className="text-sm font-medium text-gray-300 mb-1">
            {state === "error" ? "Stream error" : "Waiting for feed..."}
          </div>
          {message ? (
            <div className="text-xs text-gray-500 max-w-lg break-words">{message}</div>
          ) : null}
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

function AlertRail({ alerts, acknowledged, onAcknowledge, onDismiss }) {

  if (!alerts.length) return null

  return (
    <aside className="fixed right-4 top-24 z-40 w-[320px] max-h-[70vh] overflow-auto space-y-3 hidden xl:block">
      {alerts.map(alert => {
        const color = alert.status === "CRITICAL" ? "#ef4444" : "#f59e0b"
        const acked = acknowledged.includes(alert.id)

        return (
          <div
            key={alert.id}
            className="rounded-xl border bg-black/85 backdrop-blur p-3"
            style={{ borderColor: `${color}66` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold tracking-widest" style={{ color }}>
                {alert.status}
              </span>
              <span className="text-[11px] text-gray-400">
                {formatTime(alert.ts)}
              </span>
            </div>

            <p className="text-sm text-gray-100 mb-2">{alert.message}</p>

            <div className="text-xs text-gray-400 mb-3">
              Score {alert.score} | People {alert.personCount}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => onAcknowledge(alert.id)}
                disabled={acked}
                className="px-2 py-1 text-xs rounded border border-white/20 text-white disabled:opacity-50"
              >
                {acked ? "Acknowledged" : "Acknowledge"}
              </button>

              <button
                onClick={() => onDismiss(alert.id)}
                className="px-2 py-1 text-xs rounded border border-white/20 text-gray-300"
              >
                Dismiss
              </button>
            </div>
          </div>
        )
      })}
    </aside>
  )
}

function IncidentTimeline({ events }) {

  const items = events.filter(e => e.status !== "SAFE").slice(0, 12)

  return (
    <section className="mt-6 rounded-xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs text-gray-400 tracking-widest">INCIDENT TIMELINE</h2>
        <span className="text-xs text-gray-500">Latest 12 events</span>
      </div>

      {!items.length ? (
        <div className="text-sm text-gray-500">No incidents yet</div>
      ) : (
        <div className="overflow-x-auto">
          <div className="flex gap-3 min-w-max pb-1">
            {items.map(item => {
              const color = item.status === "CRITICAL" ? "#ef4444" : "#f59e0b"
              return (
                <div
                  key={item.id}
                  className="min-w-[200px] rounded-lg border p-3"
                  style={{ borderColor: `${color}66`, background: `${color}14` }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold" style={{ color }}>{item.status}</span>
                    <span className="text-[11px] text-gray-300">{formatTime(item.ts)}</span>
                  </div>
                  <div className="text-sm text-white mb-1">Score {item.score}</div>
                  <div className="text-xs text-gray-300">
                    {item.zoneTriggered ? "Zone breach" : "Pattern alert"}
                    {item.afterHours ? " | After-hours" : ""}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </section>
  )
}

function CameraHealthPanel({ streamOnline, lastSeenAgeMs, fps, latency }) {

  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xs text-gray-400 tracking-widest">CAMERA HEALTH</h3>
        <span
          className="text-xs font-semibold"
          style={{ color: streamOnline ? "#22c55e" : "#ef4444" }}
        >
          {streamOnline ? "ONLINE" : "OFFLINE"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <HealthMetric label="Last Frame" value={streamOnline ? "Live" : "No Signal"} />
        <HealthMetric label="FPS" value={fps ?? "-"} />
        <HealthMetric label="Latency" value={latency ? `${latency} ms` : "-"} />
        <HealthMetric label="Reconnect" value={streamOnline ? "Stable" : "Retrying"} />
      </div>
    </div>
  )
}

function HealthMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-white/10 p-2">
      <p className="text-[11px] text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-white">{value}</p>
    </div>
  )
}

function formatTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}