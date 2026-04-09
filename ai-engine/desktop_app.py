import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk
from pathlib import Path
import json

import requests

from app_runner import run_detection_loop


class QuantumEyeDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuantumEye Desktop")
        self.root.geometry("760x560")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.api_base_var = tk.StringVar(value="http://localhost:3000")
        self.email_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")
        self.camera_id_var = tk.StringVar(value="cam_1")
        self.selected_camera_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Idle")
        self.login_state_var = tk.StringVar(value="Not signed in")

        self.stop_event = None
        self.worker_thread = None
        self.log_queue = queue.Queue()
        self.token = None
        self.cameras = []

        appdata_root = Path.home() / ".quantumeye"
        appdata_root.mkdir(parents=True, exist_ok=True)
        self.auth_file = appdata_root / "auth.json"
        self._load_saved_auth()

        self._build_ui()
        self._poll_logs()

    def _load_saved_auth(self):
        if not self.auth_file.exists():
            return
        try:
            data = json.loads(self.auth_file.read_text(encoding="utf-8"))
            self.token = data.get("token")
            if data.get("api_base"):
                self.api_base_var.set(data["api_base"])
            if data.get("email"):
                self.email_var.set(data["email"])
            if self.token:
                self.login_state_var.set("Signed in (saved token)")
        except Exception:
            self.token = None

    def _save_auth(self):
        payload = {
            "api_base": self.api_base_var.get().strip(),
            "email": self.email_var.get().strip(),
            "token": self.token,
        }
        self.auth_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _clear_auth(self):
        self.token = None
        self.cameras = []
        self.camera_selector["values"] = []
        self.selected_camera_var.set("")
        self.login_state_var.set("Not signed in")
        if self.auth_file.exists():
            self.auth_file.unlink(missing_ok=True)

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=14, pady=14)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="QuantumEye Desktop Controller", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        subtitle = tk.Label(
            frame,
            text="Sign in with website account, sync your cameras, then start local detection.",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(0, 14))

        auth_frame = tk.LabelFrame(frame, text="Account Login", padx=10, pady=10)
        auth_frame.pack(fill="x", pady=(0, 10))

        tk.Label(auth_frame, text="Website API Base URL").grid(row=0, column=0, sticky="w")
        tk.Entry(auth_frame, textvariable=self.api_base_var, width=44).grid(row=0, column=1, sticky="w", padx=(10, 0))

        tk.Label(auth_frame, text="Email").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(auth_frame, textvariable=self.email_var, width=32).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(8, 0))

        tk.Label(auth_frame, text="Password").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Entry(auth_frame, textvariable=self.password_var, show="*", width=32).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(8, 0))

        auth_actions = tk.Frame(auth_frame)
        auth_actions.grid(row=3, column=1, sticky="w", pady=(10, 0))

        self.login_btn = tk.Button(auth_actions, text="Login", width=10, command=self.login)
        self.login_btn.pack(side="left")
        tk.Button(auth_actions, text="Logout", width=10, command=self.logout).pack(side="left", padx=(8, 0))
        tk.Button(auth_actions, text="Sync Cameras", width=12, command=self.sync_cameras).pack(side="left", padx=(8, 0))

        tk.Label(auth_frame, text="Session").grid(row=4, column=0, sticky="w", pady=(8, 0))
        tk.Label(auth_frame, textvariable=self.login_state_var, fg="#007a33").grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(8, 0))

        camera_frame = tk.LabelFrame(frame, text="Camera Settings", padx=10, pady=10)
        camera_frame.pack(fill="x", pady=(0, 10))

        tk.Label(camera_frame, text="Synced Cameras").grid(row=0, column=0, sticky="w")
        self.camera_selector = ttk.Combobox(
            camera_frame,
            textvariable=self.selected_camera_var,
            state="readonly",
            width=55,
            values=[],
        )
        self.camera_selector.grid(row=0, column=1, sticky="w", padx=(10, 0))

        tk.Label(camera_frame, text="Runtime Camera ID").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(camera_frame, textvariable=self.camera_id_var, width=20).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(8, 0))

        actions = tk.Frame(frame)
        actions.pack(fill="x", pady=(0, 10))

        self.start_btn = tk.Button(actions, text="Start Detection", width=16, command=self.start_detection)
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(actions, text="Stop", width=12, command=self.stop_detection, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        tk.Label(actions, text="Status:").pack(side="left", padx=(18, 6))
        tk.Label(actions, textvariable=self.status_var, fg="#007a33").pack(side="left")

        log_frame = tk.LabelFrame(frame, text="Session Log", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True)

        self.log_box = scrolledtext.ScrolledText(log_frame, height=16, state="disabled", font=("Consolas", 10))
        self.log_box.pack(fill="both", expand=True)

        help_text = (
            "Tip: add cameras from website first, then click Sync Cameras here. "
            "Press ESC in OpenCV window to stop live session."
        )
        tk.Label(frame, text=help_text, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 0))

    def _auth_headers(self):
        if not self.token:
            raise ValueError("Please login first")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def login(self):
        api_base = self.api_base_var.get().strip().rstrip("/")
        email = self.email_var.get().strip()
        password = self.password_var.get().strip()

        if not api_base or not email or not password:
            messagebox.showerror("Missing fields", "API URL, email and password are required")
            return

        try:
            res = requests.post(
                f"{api_base}/api/auth/login",
                headers={"Content-Type": "application/json"},
                json={"email": email, "password": password},
                timeout=12,
            )
            data = res.json()
        except Exception as exc:
            messagebox.showerror("Login failed", f"Request failed: {exc}")
            return

        if not res.ok:
            messagebox.showerror("Login failed", data.get("error", "Invalid credentials"))
            return

        self.token = data.get("token")
        if not self.token:
            messagebox.showerror("Login failed", "Token missing in server response")
            return

        self.password_var.set("")
        self.login_state_var.set(f"Signed in as {email}")
        self._save_auth()
        self.append_log("Login successful")
        self.sync_cameras()

    def logout(self):
        self._clear_auth()
        self.append_log("Logged out")

    def sync_cameras(self):
        api_base = self.api_base_var.get().strip().rstrip("/")
        if not api_base:
            messagebox.showerror("Missing API URL", "Set website API base URL first")
            return

        try:
            res = requests.get(
                f"{api_base}/api/cameras",
                headers=self._auth_headers(),
                timeout=12,
            )
            data = res.json()
        except Exception as exc:
            messagebox.showerror("Sync failed", f"Request failed: {exc}")
            return

        if not res.ok or not data.get("success"):
            messagebox.showerror("Sync failed", data.get("error", "Could not fetch cameras"))
            if res.status_code == 401:
                self._clear_auth()
            return

        self.cameras = data.get("cameras", [])
        camera_names = [
            f"{cam.get('name', 'Unnamed')} | {cam.get('type', 'rtsp')} | {cam.get('source', '')}"
            for cam in self.cameras
        ]
        self.camera_selector["values"] = camera_names

        if camera_names:
            self.camera_selector.current(0)
            self.selected_camera_var.set(camera_names[0])
            self.append_log(f"Synced {len(camera_names)} camera(s)")
        else:
            self.selected_camera_var.set("")
            self.append_log("No cameras found for this account")

    def append_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _status_callback(self, status, payload):
        self.log_queue.put((status, payload))

    def _poll_logs(self):
        while not self.log_queue.empty():
            status, payload = self.log_queue.get()

            if status == "started":
                self.status_var.set("Running")
                self.append_log(
                    f"Started | source={payload.get('source')} | fps={payload.get('fps'):.1f} | "
                    f"res={payload.get('resolution')} | camera_id={payload.get('camera_id')}"
                )

            elif status == "heartbeat":
                self.status_var.set(f"{payload.get('status')} | score {payload.get('score')}")
                self.append_log(
                    f"Frame {payload.get('frame')} | UI {payload.get('ui_fps')} fps | "
                    f"DET {payload.get('det_fps')} fps | People {payload.get('people')}"
                )

            elif status == "alert":
                self.append_log(
                    f"ALERT {payload.get('alert_id')} | score={payload.get('score')} | status={payload.get('status')}"
                )

            elif status == "error":
                self.status_var.set("Error")
                self.append_log(f"ERROR: {payload.get('message')}")
                self._on_worker_finished()

            elif status == "stopped":
                self.append_log(
                    f"Stopped | frames={payload.get('frames')} | total_alerts={payload.get('alerts')}"
                )
                self.status_var.set("Stopped")
                self._on_worker_finished()

        self.root.after(200, self._poll_logs)

    def _run_worker(self, source, camera_id):
        try:
            run_detection_loop(
                source=source,
                camera_id=camera_id,
                camera_rules=self._selected_camera_rules(),
                stop_event=self.stop_event,
                on_status=self._status_callback,
            )
        except Exception as exc:
            self.log_queue.put(("error", {"message": str(exc)}))

    def _selected_camera_rules(self):
        selected = self.camera_selector.current()
        if selected < 0 or selected >= len(self.cameras):
            return {}
        return self.cameras[selected].get("rules", {}) or {}

    def start_detection(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("QuantumEye", "Detection is already running.")
            return

        if not self.cameras:
            messagebox.showerror("No cameras", "No synced cameras available. Please login and sync first.")
            return

        selected = self.camera_selector.current()
        if selected < 0 or selected >= len(self.cameras):
            messagebox.showerror("No selection", "Select a camera from Synced Cameras")
            return

        source = self.cameras[selected].get("source")
        if source is None or str(source).strip() == "":
            messagebox.showerror("Invalid source", "Selected camera has no source URL")
            return

        camera_id = self.camera_id_var.get().strip() or str(self.cameras[selected].get("_id") or "cam_1")

        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(source, camera_id),
            daemon=True,
        )
        self.worker_thread.start()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("Starting")

    def _on_worker_finished(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.stop_event = None
        self.worker_thread = None

    def stop_detection(self):
        if self.stop_event:
            self.append_log("Stop requested by user")
            self.status_var.set("Stopping")
            self.stop_event.set()

    def on_close(self):
        if self.stop_event:
            self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    QuantumEyeDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
