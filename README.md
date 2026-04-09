# VisionIQ

VisionIQ is an AI surveillance platform that turns raw camera feeds into actionable security intelligence.

It combines real-time computer vision, configurable camera rules, incident playback, and an operator-first dashboard for faster response.

## Why This Project Matters

Traditional CCTV systems record everything and explain nothing.

VisionIQ focuses on what security teams actually need:
- Live risk scoring instead of passive monitoring
- Rule-based detection behavior per camera
- Alert noise reduction with cooldown and acknowledgement flow
- Incident playback clips for quick investigation

## What I Built

### Real-Time AI Detection Engine
- Processes live camera streams with YOLO-based detection
- Tracks people count and behavior signals
- Scores threat severity in real time
- Streams annotated frames and telemetry over websocket

### Camera-Level Rule System
- Restricted zone monitoring
- Open hours and after-hours violation detection
- Maximum people threshold per camera
- Per-camera notes and operating profile

### Centralized Security Dashboard
- Camera management with source validation
- Rule settings modal per camera
- Live monitoring panel with threat timeline
- Alert rail with acknowledge and dismiss controls

### Incident Response Workflow
- Alert throttling to reduce spam: one alert every 5 minutes per camera by default
- Acknowledgement can permit immediate next alert cycle when needed
- Incident playback stored as MP4 clips (instead of only snapshots)

### Notification Integration
- Browser push notifications for suspicious and critical events
- Dashboard API integration with AI engine alert emission

## Product Demo Narrative

1. Operator adds a camera and defines security rules.
2. AI engine starts processing stream and scoring risk live.
3. When a rule breach or critical signal occurs, an alert is generated.
4. Alert appears in dashboard and alerts page with incident playback video.
5. Operator acknowledges alert, investigates quickly, and continues monitoring with reduced alert fatigue.

## Architecture

VisionIQ runs as two services:

- Dashboard service
  - Next.js application
  - Auth, camera and rule configuration, alert UX, push APIs
- AI engine service
  - FastAPI + OpenCV + YOLO pipeline
  - Detection, scoring, rules evaluation, incident media generation

## Tech Stack

### Frontend and API
- Next.js
- React
- Tailwind CSS
- MongoDB + Mongoose
- JWT authentication
- Web Push

### AI and Streaming
- Python
- FastAPI + Uvicorn
- OpenCV
- Ultralytics YOLO
- NumPy

## Quick Start

### 1. Start Dashboard

```powershell
cd dashboard
npm install
```

Create dashboard environment file:

```powershell
@"
MONGO_URI=mongodb://127.0.0.1:27017/visioniq
JWT_SECRET=replace_with_a_long_random_secret
VISIONIQ_ENGINE_URL=http://localhost:8010
QUANTUMEYE_ENGINE_URL=http://localhost:8010
NEXT_PUBLIC_AI_ENGINE_URL=http://localhost:8010
"@ | Set-Content .env.local
```

Run dashboard:

```powershell
npm run dev
```

### 2. Start AI Engine

```powershell
cd ..\ai-engine
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
$env:DASHBOARD_API_URL="http://localhost:3000"
uvicorn stream_server:app --host 0.0.0.0 --port 8010 --reload
```

Open:
- Dashboard: http://localhost:3000
- AI engine: http://localhost:8010

## Project Highlights for Recruiters

- End-to-end system design across frontend, backend, and CV pipeline
- Real-time stream processing and event-driven UI updates
- Practical security UX decisions: cooldowns, acknowledgement, playback-first investigation
- Production-minded integration patterns between independent services

## Existing Detailed Docs

- [dashboard/PUSH_NOTIFICATIONS_SETUP.md](dashboard/PUSH_NOTIFICATIONS_SETUP.md)
- [ai-engine/DESKTOP_APP.md](ai-engine/DESKTOP_APP.md)

## Next Improvements

- Polygon-drawn restricted zones per camera
- Multi-camera live wall with per-feed health indicators
- Role-based access control for security teams
- Incident export bundles for audits

## License

No license file is currently included. Add one before open-source release.
