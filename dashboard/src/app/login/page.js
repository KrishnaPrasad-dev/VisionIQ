"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState("")
  const [mounted, setMounted]   = useState(false)

  useEffect(() => { setMounted(true) }, [])

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!username || !password) { setError("Please enter your credentials"); return }
    setError("")
    setLoading(true)
    await new Promise(r => setTimeout(r, 1600))
    setLoading(false)
    router.push("/dashboard")
  }

  return (
    <main style={{
      minHeight: "100vh",
      background: "#080c10",
      display: "flex",
      fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
      position: "relative",
      overflow: "hidden",
    }}>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }

        @keyframes fadeUp   { from { opacity:0; transform:translateY(24px) } to { opacity:1; transform:translateY(0) } }
        @keyframes fadeIn   { from { opacity:0 } to { opacity:1 } }
        @keyframes spin     { to { transform:rotate(360deg) } }
        @keyframes glow-pulse { 0%,100% { opacity:0.5 } 50% { opacity:1 } }
        @keyframes slide-in { from { opacity:0; transform:translateX(-8px) } to { opacity:1; transform:translateX(0) } }

        .left-panel  { animation: fadeIn 1s ease forwards; }
        .right-panel { animation: fadeUp 0.7s ease 0.2s both; }

        .input-field { transition: all 0.2s ease; }
        .input-field:focus { outline: none; border-color: rgba(59,130,246,0.6) !important; background: rgba(59,130,246,0.05) !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.08); }
        .input-field::placeholder { color: rgba(255,255,255,0.2); }

        .login-btn { transition: all 0.2s ease; }
        .login-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 30px rgba(59,130,246,0.35) !important; }
        .login-btn:active:not(:disabled) { transform: translateY(0); }
        .login-btn:disabled { opacity: 0.7; cursor: not-allowed; }

        .stat-card { transition: all 0.25s ease; }
        .stat-card:hover { transform: translateY(-2px); background: rgba(255,255,255,0.06) !important; }

        input:-webkit-autofill { -webkit-box-shadow: 0 0 0 100px #0f1923 inset !important; -webkit-text-fill-color: #fff !important; }
      `}</style>

      {/* Background orbs */}
      <div style={{ position:"absolute", inset:0, overflow:"hidden", pointerEvents:"none" }}>
        <div style={{
          position:"absolute", width:700, height:700, borderRadius:"50%",
          background:"radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)",
          top:"-15%", left:"15%", filter:"blur(60px)",
        }} />
        <div style={{
          position:"absolute", width:500, height:500, borderRadius:"50%",
          background:"radial-gradient(circle, rgba(99,179,237,0.05) 0%, transparent 70%)",
          bottom:"-10%", right:"5%", filter:"blur(60px)",
        }} />
        <div style={{
          position:"absolute", width:350, height:350, borderRadius:"50%",
          background:"radial-gradient(circle, rgba(16,185,129,0.04) 0%, transparent 70%)",
          top:"50%", left:"3%", filter:"blur(50px)",
        }} />
      </div>

      {/* Grid */}
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none",
        backgroundImage:`linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.012) 1px, transparent 1px)`,
        backgroundSize:"64px 64px",
      }} />

      {/* LEFT PANEL */}
      <div className="left-panel" style={{
        flex:1, display:"flex", flexDirection:"column", justifyContent:"space-between",
        padding:"48px 56px",
        borderRight:"1px solid rgba(255,255,255,0.05)",
        position:"relative",
      }}>

        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{
            width:38, height:38, borderRadius:10,
            background:"linear-gradient(135deg, #3b82f6, #1d4ed8)",
            display:"flex", alignItems:"center", justifyContent:"center",
            fontSize:18, boxShadow:"0 4px 20px rgba(59,130,246,0.4)",
          }}>◉</div>
          <span style={{ fontSize:20, fontWeight:700, color:"#fff", letterSpacing:"-0.02em" }}>
            Vision<span style={{ color:"#3b82f6" }}>IQ</span>
          </span>
        </div>

        {/* Hero content */}
        <div>
          <div style={{
            display:"inline-flex", alignItems:"center", gap:8,
            padding:"6px 14px", borderRadius:99,
            background:"rgba(16,185,129,0.1)", border:"1px solid rgba(16,185,129,0.2)",
            marginBottom:28,
          }}>
            <div style={{ width:6, height:6, borderRadius:"50%", background:"#10b981", animation:"glow-pulse 2s infinite" }} />
            <span style={{ fontSize:11, color:"#10b981", fontWeight:600, letterSpacing:"0.05em" }}>SYSTEM ACTIVE</span>
          </div>

          <h2 style={{
            fontSize:44, fontWeight:800, color:"#fff", lineHeight:1.15,
            letterSpacing:"-0.03em", marginBottom:18,
          }}>
            AI-Powered<br />
            <span style={{ color:"#3b82f6" }}>Surveillance</span><br />
            Intelligence
          </h2>

          <p style={{
            fontSize:15, color:"rgba(255,255,255,0.4)", lineHeight:1.75,
            maxWidth:360,
          }}>
            Real-time threat detection and monitoring powered by computer vision. See smarter, stay safer.
          </p>

          {/* Stats */}
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginTop:44 }}>
            {[
              { value:"20+",  label:"FPS Detection" },
              { value:"98%",  label:"Accuracy Rate" },
              { value:"<2s",  label:"Alert Response" },
            ].map(({ value, label }) => (
              <div key={label} className="stat-card" style={{
                padding:"18px 16px", borderRadius:12,
                background:"rgba(255,255,255,0.03)",
                border:"1px solid rgba(255,255,255,0.07)",
              }}>
                <div style={{ fontSize:24, fontWeight:800, color:"#fff", letterSpacing:"-0.03em" }}>{value}</div>
                <div style={{ fontSize:11, color:"rgba(255,255,255,0.3)", marginTop:4, fontWeight:500 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ fontSize:12, color:"rgba(255,255,255,0.12)", fontWeight:500 }}>
          Tech Horizon 1.0 &nbsp;·&nbsp; See Smarter. Stay Safer.
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div style={{
        width:480, display:"flex", flexDirection:"column",
        alignItems:"center", justifyContent:"center",
        padding:"48px",
      }}>
        <div className="right-panel" style={{ width:"100%" }}>

          <div style={{ marginBottom:36 }}>
            <h1 style={{
              fontSize:26, fontWeight:700, color:"#fff",
              letterSpacing:"-0.02em", marginBottom:8,
            }}>
              Welcome back
            </h1>
            <p style={{ fontSize:14, color:"rgba(255,255,255,0.35)" }}>
              Sign in to access your surveillance dashboard
            </p>
          </div>

          <form onSubmit={handleLogin} style={{ display:"flex", flexDirection:"column", gap:16 }}>

            <div style={{ display:"flex", flexDirection:"column", gap:7 }}>
              <label style={{ fontSize:13, fontWeight:500, color:"rgba(255,255,255,0.55)" }}>Username</label>
              <input
                className="input-field"
                type="text"
                value={username}
                onChange={e => { setUsername(e.target.value); setError("") }}
                placeholder="Enter your username"
                style={{
                  width:"100%", padding:"13px 16px",
                  background:"rgba(255,255,255,0.05)",
                  border:"1px solid rgba(255,255,255,0.09)",
                  borderRadius:10, color:"#fff",
                  fontSize:14, fontFamily:"inherit",
                }}
              />
            </div>

            <div style={{ display:"flex", flexDirection:"column", gap:7 }}>
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <label style={{ fontSize:13, fontWeight:500, color:"rgba(255,255,255,0.55)" }}>Password</label>
                <span style={{ fontSize:12, color:"#3b82f6", cursor:"pointer", fontWeight:500 }}>Forgot password?</span>
              </div>
              <input
                className="input-field"
                type="password"
                value={password}
                onChange={e => { setPassword(e.target.value); setError("") }}
                placeholder="Enter your password"
                style={{
                  width:"100%", padding:"13px 16px",
                  background:"rgba(255,255,255,0.05)",
                  border:"1px solid rgba(255,255,255,0.09)",
                  borderRadius:10, color:"#fff",
                  fontSize:14, fontFamily:"inherit",
                }}
              />
            </div>

            {error && (
              <div style={{
                padding:"11px 14px", borderRadius:8, animation:"slide-in 0.2s ease",
                background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.2)",
                fontSize:13, color:"#f87171", display:"flex", alignItems:"center", gap:8,
              }}>
                <span>⚠</span> {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="login-btn"
              style={{
                marginTop:6, padding:"14px",
                background:"linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
                border:"none", borderRadius:10,
                color:"#fff", fontSize:14, fontWeight:600,
                fontFamily:"inherit", cursor:"pointer",
                boxShadow:"0 4px 20px rgba(59,130,246,0.2)",
                display:"flex", alignItems:"center", justifyContent:"center", gap:10,
              }}
            >
              {loading ? (
                <>
                  <div style={{
                    width:16, height:16, borderRadius:"50%",
                    border:"2px solid rgba(255,255,255,0.3)",
                    borderTopColor:"#fff",
                    animation:"spin 0.7s linear infinite",
                  }} />
                  Authenticating...
                </>
              ) : "Sign In →"}
            </button>

          </form>

          <div style={{ display:"flex", alignItems:"center", gap:14, margin:"28px 0" }}>
            <div style={{ flex:1, height:1, background:"rgba(255,255,255,0.06)" }} />
            <span style={{ fontSize:12, color:"rgba(255,255,255,0.18)", fontWeight:500 }}>prototype access</span>
            <div style={{ flex:1, height:1, background:"rgba(255,255,255,0.06)" }} />
          </div>

          {/* Demo hint */}
          <div style={{
            padding:"14px 16px", borderRadius:10,
            background:"rgba(59,130,246,0.06)",
            border:"1px solid rgba(59,130,246,0.13)",
            display:"flex", gap:12,
          }}>
            <span style={{ fontSize:15, color:"#3b82f6", marginTop:1 }}>ℹ</span>
            <div>
              <div style={{ fontSize:13, fontWeight:600, color:"rgba(255,255,255,0.65)", marginBottom:3 }}>Demo Mode</div>
              <div style={{ fontSize:12, color:"rgba(255,255,255,0.3)", lineHeight:1.6 }}>
                Any username and password will grant access to the dashboard.
              </div>
            </div>
          </div>

          <p style={{ textAlign:"center", marginTop:32, fontSize:12, color:"rgba(255,255,255,0.12)" }}>
            VisionIQ © 2026 · All rights reserved
          </p>

        </div>
      </div>

    </main>
  )
}