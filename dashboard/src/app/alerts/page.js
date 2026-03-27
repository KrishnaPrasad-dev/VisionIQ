"use client"
import { useState } from "react"
import Navbar from "../../components/Navbar"
import GridBackground from "../../components/GridBackground"
import useQuantumEye from "../../hooks/useQuantumEye"

const AI_ENGINE = "http://localhost:8000"

const DEMO_ALERTS = [
  { timestamp: "2026-03-14T12:45:21", status: "CRITICAL",   score: 82, person_count: 4, snapshot_path: null },
  { timestamp: "2026-03-14T12:41:09", status: "SUSPICIOUS", score: 55, person_count: 2, snapshot_path: null },
  { timestamp: "2026-03-14T11:42:19", status: "CRITICAL",   score: 88, person_count: 5, snapshot_path: null },
]

const STATUS = {
  CRITICAL:   { color: "#f87171", bg: "rgba(248,113,113,0.08)", border: "rgba(248,113,113,0.25)" },
  SUSPICIOUS: { color: "#fbbf24", bg: "rgba(251,191,36,0.08)",  border: "rgba(251,191,36,0.25)"  },
}

const FILTERS = ["ALL", "CRITICAL", "SUSPICIOUS"]

function snapshotUrl(path) {
  if (!path) return null
  if (path.startsWith("http")) return path
  // path from AI engine is like "snapshots/alert_20260314_124521.jpg"
  // served at http://localhost:8000/snapshots/alert_20260314_124521.jpg
  const clean = path.replace(/^\//, "")
  return `${AI_ENGINE}/${clean}`
}

function fmt(ts) {
  try {
    const d = new Date(ts)
    return {
      time: d.toLocaleTimeString("en-US", { hour12: false }),
      date: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    }
  } catch { return { time: ts, date: "" } }
}

function SnapshotThumb({ path, status }) {
  const [err, setErr] = useState(false)
  const url = snapshotUrl(path)
  if (!url || err) {
    return (
      <div style={{ width:"100%", height:"100%", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:8 }}>
        <span style={{ fontSize:28, opacity:0.1 }}>◉</span>
        <span style={{ fontSize:10, color:"rgba(255,255,255,0.12)", letterSpacing:"0.15em" }}>NO SNAPSHOT</span>
      </div>
    )
  }
  return (
    <img
      src={url}
      alt="alert snapshot"
      onError={() => setErr(true)}
      style={{ width:"100%", height:"100%", objectFit:"cover", display:"block" }}
    />
  )
}

export default function AlertsPage() {
  const data = useQuantumEye()
  const [filter, setFilter] = useState("ALL")
  const [view,   setView]   = useState("grid")
  const [modal,  setModal]  = useState(null)

  // Only keep CRITICAL and SUSPICIOUS — filter out SAFE at source
  const rawAlerts = (data?.alerts?.length ? data.alerts : DEMO_ALERTS)
    .filter(a => a.status === "CRITICAL" || a.status === "SUSPICIOUS")

  const alerts = filter === "ALL" ? rawAlerts : rawAlerts.filter(a => a.status === filter)

  const counts = {
    ALL:        rawAlerts.length,
    CRITICAL:   rawAlerts.filter(a => a.status === "CRITICAL").length,
    SUSPICIOUS: rawAlerts.filter(a => a.status === "SUSPICIOUS").length,
  }

  return (
    <main style={{ minHeight:"100vh", background:"#080c10", color:"#fff", fontFamily:"'Segoe UI', system-ui, sans-serif" }}>
      <GridBackground />
      <Navbar />

      <style>{`
        @keyframes fadeUp  { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
        @keyframes glow-pulse { 0%,100%{opacity:0.5} 50%{opacity:1} }
        .alert-card { transition:all 0.2s ease; animation:fadeUp 0.4s ease both; }
        .alert-card:hover { transform:translateY(-3px); border-color:rgba(255,255,255,0.18) !important; }
        .filter-btn { transition:all 0.2s ease; cursor:pointer; }
        .filter-btn:hover { background:rgba(255,255,255,0.07) !important; }
        .view-btn   { transition:all 0.15s ease; cursor:pointer; }
        .snap-wrap:hover .snap-overlay { opacity:1 !important; }
      `}</style>

      <div style={{ maxWidth:1300, margin:"0 auto", padding:"120px 24px 60px" }}>

        {/* HEADER */}
        <div style={{ marginBottom:36 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:10 }}>
            <div style={{ width:6, height:6, borderRadius:"50%", background:"#f87171", animation:"glow-pulse 2s infinite" }} />
            <span style={{ fontSize:11, color:"rgba(255,255,255,0.3)", letterSpacing:"0.15em", fontWeight:500 }}>SECURITY EVENTS</span>
          </div>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end", flexWrap:"wrap", gap:16 }}>
            <div>
              <h1 style={{ fontSize:28, fontWeight:700, letterSpacing:"-0.02em", margin:0 }}>Alert History</h1>
              <p style={{ fontSize:14, color:"rgba(255,255,255,0.35)", marginTop:6 }}>
                Critical and suspicious threat events detected by AI
              </p>
            </div>
            <div style={{ display:"flex", gap:4, background:"rgba(255,255,255,0.04)", borderRadius:10, padding:4, border:"1px solid rgba(255,255,255,0.07)" }}>
              {[["grid","⊞  Grid"],["list","≡  List"]].map(([v,label])=>(
                <button key={v} className="view-btn" onClick={()=>setView(v)} style={{
                  padding:"7px 16px", borderRadius:7, border:"none",
                  background: view===v ? "rgba(255,255,255,0.1)" : "transparent",
                  color: view===v ? "#fff" : "rgba(255,255,255,0.35)",
                  fontSize:12, fontWeight:600, fontFamily:"inherit", cursor:"pointer",
                  boxShadow: view===v ? "0 1px 4px rgba(0,0,0,0.3)" : "none",
                }}>{label}</button>
              ))}
            </div>
          </div>
        </div>

        {/* STAT CARDS — 3 only, no SAFE */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12, marginBottom:28 }}>
          {[
            { label:"Total Threats", value:counts.ALL,        color:"#fff",    bg:"rgba(255,255,255,0.04)" },
            { label:"Critical",      value:counts.CRITICAL,   color:"#f87171", bg:"rgba(248,113,113,0.05)" },
            { label:"Suspicious",    value:counts.SUSPICIOUS, color:"#fbbf24", bg:"rgba(251,191,36,0.05)"  },
          ].map(({label,value,color,bg})=>(
            <div key={label} style={{ padding:"18px 20px", borderRadius:12, background:bg, border:"1px solid rgba(255,255,255,0.07)" }}>
              <div style={{ fontSize:28, fontWeight:800, color, letterSpacing:"-0.03em" }}>{value}</div>
              <div style={{ fontSize:12, color:"rgba(255,255,255,0.3)", marginTop:4, fontWeight:500 }}>{label}</div>
            </div>
          ))}
        </div>

        {/* FILTER TABS */}
        <div style={{ display:"flex", gap:8, marginBottom:24 }}>
          {FILTERS.map(f=>{
            const active = filter===f
            const cfg    = STATUS[f] || { color:"#fff", bg:"rgba(255,255,255,0.06)", border:"rgba(255,255,255,0.12)" }
            return(
              <button key={f} className="filter-btn" onClick={()=>setFilter(f)} style={{
                padding:"7px 18px", borderRadius:99, border:"1px solid",
                borderColor: active ? cfg.border : "rgba(255,255,255,0.08)",
                background:  active ? cfg.bg     : "transparent",
                color:       active ? cfg.color  : "rgba(255,255,255,0.4)",
                fontSize:12, fontWeight:600, fontFamily:"inherit", letterSpacing:"0.04em",
              }}>
                {f} <span style={{ opacity:0.6, fontSize:11 }}>({counts[f]??0})</span>
              </button>
            )
          })}
        </div>

        {/* NO RESULTS */}
        {alerts.length===0 && (
          <div style={{ textAlign:"center", padding:"80px 0", color:"rgba(255,255,255,0.2)", fontSize:14 }}>
            No threat alerts recorded yet
          </div>
        )}

        {/* GRID VIEW */}
        {alerts.length>0 && view==="grid" && (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))", gap:16 }}>
            {alerts.map((alert,i)=>{
              const cfg = STATUS[alert.status]||STATUS.SUSPICIOUS
              const {time,date} = fmt(alert.timestamp)
              const hasSnap = !!snapshotUrl(alert.snapshot_path)
              return(
                <div key={i} className="alert-card" style={{
                  background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)",
                  borderRadius:14, overflow:"hidden", animationDelay:`${i*0.05}s`,
                }}>
                  <div
                    className="snap-wrap"
                    onClick={()=>hasSnap && setModal(alert)}
                    style={{ aspectRatio:"16/9", background:"rgba(0,0,0,0.6)", position:"relative", cursor:hasSnap?"pointer":"default" }}
                  >
                    <SnapshotThumb path={alert.snapshot_path} status={alert.status} />

                    {hasSnap && (
                      <div className="snap-overlay" style={{
                        position:"absolute", inset:0, background:"rgba(0,0,0,0.5)",
                        display:"flex", alignItems:"center", justifyContent:"center",
                        opacity:0, transition:"opacity 0.2s",
                      }}>
                        <span style={{ fontSize:12, fontWeight:600, color:"#fff", padding:"8px 18px", borderRadius:99, background:"rgba(255,255,255,0.15)", border:"1px solid rgba(255,255,255,0.3)" }}>
                          🔍 View Full
                        </span>
                      </div>
                    )}

                    <div style={{
                      position:"absolute", top:10, right:10,
                      padding:"4px 10px", borderRadius:99,
                      background:cfg.bg, border:`1px solid ${cfg.border}`,
                      fontSize:10, fontWeight:700, color:cfg.color, letterSpacing:"0.06em",
                    }}>{alert.status}</div>
                  </div>

                  <div style={{ padding:16 }}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
                      <div>
                        <div style={{ fontSize:14, fontWeight:600 }}>{time}</div>
                        <div style={{ fontSize:11, color:"rgba(255,255,255,0.3)", marginTop:2 }}>{date}</div>
                      </div>
                      <div style={{ width:8, height:8, borderRadius:"50%", background:cfg.color, boxShadow:`0 0 8px ${cfg.color}` }} />
                    </div>
                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
                      {[
                        { label:"THREAT SCORE", value:alert.score,                              color:cfg.color },
                        { label:"PERSONS",       value:alert.person_count??alert.people??0,     color:"#fff"    },
                      ].map(({label,value,color})=>(
                        <div key={label} style={{ padding:"10px 12px", background:"rgba(255,255,255,0.03)", borderRadius:8, border:"1px solid rgba(255,255,255,0.06)" }}>
                          <div style={{ fontSize:10, color:"rgba(255,255,255,0.3)", marginBottom:3 }}>{label}</div>
                          <div style={{ fontSize:18, fontWeight:700, color }}>{value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* LIST VIEW */}
        {alerts.length>0 && view==="list" && (
          <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
            <div style={{
              display:"grid", gridTemplateColumns:"56px 2fr 1fr 1fr 1fr 80px",
              padding:"10px 16px", gap:16,
              fontSize:10, color:"rgba(255,255,255,0.25)", letterSpacing:"0.1em", fontWeight:600,
              borderBottom:"1px solid rgba(255,255,255,0.06)",
            }}>
              <span>SNAP</span><span>TIMESTAMP</span><span>STATUS</span><span>SCORE</span><span>PERSONS</span><span></span>
            </div>
            {alerts.map((alert,i)=>{
              const cfg = STATUS[alert.status]||STATUS.SUSPICIOUS
              const {time,date} = fmt(alert.timestamp)
              const url = snapshotUrl(alert.snapshot_path)
              return(
                <div key={i} className="alert-card" style={{
                  display:"grid", gridTemplateColumns:"56px 2fr 1fr 1fr 1fr 80px",
                  alignItems:"center", gap:16, padding:"12px 16px", borderRadius:10,
                  background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.07)",
                  animationDelay:`${i*0.04}s`,
                }}>
                  <div onClick={()=>url&&setModal(alert)} style={{
                    width:48, height:36, borderRadius:6, overflow:"hidden",
                    background:"rgba(0,0,0,0.5)", border:"1px solid rgba(255,255,255,0.08)",
                    cursor:url?"pointer":"default", flexShrink:0,
                  }}>
                    {url
                      ? <img src={url} alt="" onError={e=>e.target.style.display="none"} style={{ width:"100%", height:"100%", objectFit:"cover" }} />
                      : <div style={{ width:"100%", height:"100%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, opacity:0.2 }}>◉</div>
                    }
                  </div>
                  <div>
                    <span style={{ fontSize:14, fontWeight:500 }}>{time}</span>
                    <span style={{ fontSize:12, color:"rgba(255,255,255,0.3)", marginLeft:10 }}>{date}</span>
                  </div>
                  <span style={{
                    display:"inline-flex", alignItems:"center", gap:6,
                    padding:"4px 10px", borderRadius:99,
                    background:cfg.bg, border:`1px solid ${cfg.border}`,
                    fontSize:11, fontWeight:600, color:cfg.color, width:"fit-content",
                  }}>
                    <span style={{ width:5, height:5, borderRadius:"50%", background:cfg.color, display:"inline-block" }} />
                    {alert.status}
                  </span>
                  <span style={{ fontSize:16, fontWeight:700, color:cfg.color }}>{alert.score}</span>
                  <span style={{ fontSize:14, color:"rgba(255,255,255,0.6)" }}>{alert.person_count??alert.people??0}</span>
                  <button onClick={()=>url&&setModal(alert)} disabled={!url} style={{
                    padding:"6px 14px", borderRadius:7,
                    background:url?"rgba(255,255,255,0.06)":"transparent",
                    border:"1px solid rgba(255,255,255,0.1)",
                    color:url?"rgba(255,255,255,0.5)":"rgba(255,255,255,0.15)",
                    fontSize:11, fontWeight:500, fontFamily:"inherit",
                    cursor:url?"pointer":"not-allowed",
                  }}>{url?"View":"—"}</button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* LIGHTBOX MODAL */}
      {modal && (
        <div onClick={()=>setModal(null)} style={{
          position:"fixed", inset:0, zIndex:999,
          background:"rgba(0,0,0,0.92)",
          display:"flex", alignItems:"center", justifyContent:"center",
          animation:"fadeIn 0.2s ease", padding:24,
        }}>
          <div onClick={e=>e.stopPropagation()} style={{ maxWidth:900, width:"100%", position:"relative" }}>
            <button onClick={()=>setModal(null)} style={{
              position:"absolute", top:-44, right:0,
              background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.15)",
              borderRadius:8, color:"#fff", fontSize:13, fontWeight:600,
              padding:"6px 16px", cursor:"pointer", fontFamily:"inherit",
            }}>✕ Close</button>
            <div style={{ borderRadius:14, overflow:"hidden", border:`1px solid ${(STATUS[modal.status]||STATUS.SUSPICIOUS).border}` }}>
              <img src={snapshotUrl(modal.snapshot_path)} alt="snapshot" style={{ width:"100%", display:"block" }} />
            </div>
            <div style={{
              marginTop:14, display:"flex", gap:16, flexWrap:"wrap",
              padding:"14px 18px", borderRadius:12,
              background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)",
            }}>
              {[
                { label:"STATUS",       value:modal.status,                             color:(STATUS[modal.status]||STATUS.SUSPICIOUS).color },
                { label:"THREAT SCORE", value:modal.score,                              color:"#fff" },
                { label:"PERSONS",      value:modal.person_count??modal.people??0,      color:"#fff" },
                { label:"TIME",         value:fmt(modal.timestamp).time,                color:"#fff" },
              ].map(({label,value,color})=>(
                <div key={label} style={{ flex:1, minWidth:100 }}>
                  <div style={{ fontSize:10, color:"rgba(255,255,255,0.3)", letterSpacing:"0.1em", marginBottom:4 }}>{label}</div>
                  <div style={{ fontSize:18, fontWeight:700, color }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  )
}