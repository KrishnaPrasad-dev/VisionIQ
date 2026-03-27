# QuantumEye Desktop App (MVP)

This desktop app wraps the existing AI engine with a simple native UI.

## Features
- Login with website account credentials
- Sync cameras from website account
- Start detection from the selected synced camera source
- Start and stop detection from desktop controls
- Uses existing QuantumEye pipeline, alerting, and overlays
- Keeps baseline learning and alert history behavior

## Run
1. Open terminal in `ai-engine`
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start desktop app:

```powershell
python desktop_app.py
```

## Source Inputs
1. Add cameras from website first
2. In desktop app, login with the same account
3. Click `Sync Cameras`
4. Select camera from dropdown and start detection

## Account Linking
- Default website API base URL: `http://localhost:3000`
- Desktop stores token locally in `%USERPROFILE%\\.quantumeye\\auth.json`
- Logout clears local token and camera cache

## Stop Session
- In desktop app: click `Stop`
- In OpenCV live window: press `ESC`

## Build Windows EXE (optional)
Install PyInstaller:

```powershell
pip install pyinstaller
```

Build command:

```powershell
pyinstaller --noconfirm --onefile --windowed --name QuantumEyeDesktop desktop_app.py
```

Output executable:
- `dist/QuantumEyeDesktop.exe`

## Notes
- Ensure model file exists at `models/yolov8n.pt`
- First model load can take a few seconds
- Webcam access may require camera permission in Windows settings
- If camera sync fails with `401`, login again to refresh token
