"""
main.py — pi_productivity

Adds a FastAPI-based web app that runs alongside your existing pipeline.
- Shows Sense HAT diagnostics (or graceful fallbacks when not present)
- Shows current mode (pulls from your project if available)
- Shows camera preview endpoint
- Shows Motion events/tasks (tails motion log)
- Cute responsive Corgi mascot reacts to activity/mode

How it works
------------
• On startup, this file also writes minimal front-end assets to ./web/ (index.html, app.js, styles.css, corgi.svg) if they don't exist, so you can keep a single-file entrypoint.
• The web app runs on 0.0.0.0 (LAN-accessible) at port 8090 by default (override via env WEBAPP_PORT).
• The server runs in a background thread so your other tasks can continue to run.
• When the window is narrow/small, the UI collapses to only Corgi + measures + time.

Requirements (install as needed)
--------------------------------
python -m pip install fastapi uvicorn[standard] jinja2 watchdog opencv-python numpy
# Optional (on Raspberry Pi OS, prefer system packages for OpenCV if heavy):
# sudo apt-get install python3-opencv

Camera notes
------------
• If OpenCV can't open /dev/video0, the /camera.jpg returns a 1x1 placeholder.
• If you already run Motion with an MJPEG stream, you can swap the <img> to that URL.

Sense HAT notes
---------------
• If Sense HAT not available, fake readings are provided.

Motion events
-------------
• Tails /var/log/motion/motion.log (Debian default) for last N events. Adjust MOTION_LOG below if yours differs.

"""

from __future__ import annotations
import asyncio
import os
import io
import cv2  # type: ignore
import json
import time
import enum
import threading
import xml.etree.ElementTree as ET
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------- Configuration ----------------
WEB_DIR = Path(__file__).parent / "web"
TEMPLATES_DIR = WEB_DIR
STATIC_DIR = WEB_DIR / "static"
DOG_SVG_PATH = STATIC_DIR / "dog.svg"
MOTION_LOG = Path("/var/log/motion/motion.log")  # adjust if needed
PORT = int(os.getenv("WEBAPP_PORT", "8090"))
HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")

WEB_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Sense HAT (optional) ----------------
class SenseFacade:
    def __init__(self):
        self.ok = False
        self.err = None
        try:
            # Try sense-hat first; on Bookworm it may be 'sense_emu' or 'sense_hat'.
            from sense_hat import SenseHat  # type: ignore
            self.sense = SenseHat()
            self.ok = True
        except Exception as e:  # noqa: BLE001
            self.sense = None
            self.err = str(e)

    def readings(self) -> Dict[str, Any]:
        if self.ok and self.sense:
            try:
                t = self.sense.get_temperature()
                h = self.sense.get_humidity()
                p = self.sense.get_pressure()
                return {
                    "temperature": round(float(t), 1),
                    "humidity": round(float(h), 1),
                    "pressure": round(float(p), 1),
                    "available": True,
                }
            except Exception as e:  # noqa: BLE001
                return {"available": False, "error": f"SenseHat read failed: {e}"}
        # Fallback fake data
        return {
            "temperature": 25.0,
            "humidity": 50.0,
            "pressure": 1013.0,
            "available": False,
            "error": self.err or "Sense HAT not detected — using fake data",
        }

# ---------------- Mode detection (plugs into your project) ----------------
class Mode(str, enum.Enum):
    IDLE = "IDLE"
    FOCUS = "FOCUS"
    BREAK = "BREAK"
    ALERT = "ALERT"

_current_mode: Mode = Mode.IDLE

# Try to import a mode provider from your project if present
# Expose a lightweight getter so the UI reflects your real state.

def get_current_mode() -> str:
    global _current_mode
    try:
        # Example: your project may expose something like this
        # from sense_modes import current_mode  # type: ignore
        # return str(current_mode())
        pass
    except Exception:
        pass
    return str(_current_mode)

# Allow updating mode from elsewhere in your code

def set_mode(new_mode: str | Mode) -> None:
    global _current_mode
    try:
        _current_mode = Mode(str(new_mode))
    except Exception:
        _current_mode = Mode.IDLE

# ---------------- Camera helpers ----------------
class Camera:
    def __init__(self, index: int = 0):
        self.index = index
        self.cap = None
        self.lock = threading.Lock()
        self._open()

    def _open(self):
        try:
            self.cap = cv2.VideoCapture(self.index)
            if not self.cap or not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None

    def read_jpeg(self) -> Optional[bytes]:
        with self.lock:
            if not self.cap:
                self._open()
                if not self.cap:
                    return None
            ok, frame = self.cap.read()
            if not ok:
                return None
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                return None
            return bytes(buf)

# ---------------- Motion log tail ----------------
class MotionTailer:
    def __init__(self, path: Path, max_lines: int = 50):
        self.path = path
        self.max_lines = max_lines
        self.lines: List[str] = []
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self._stop.set()

    def snapshot(self) -> List[str]:
        return list(self.lines[-self.max_lines :])

    def _run(self):
        try:
            # On first run, read last max_lines from file if present
            if self.path.exists():
                with self.path.open("r", errors="ignore") as f:
                    self.lines = f.readlines()[-self.max_lines :]
            # Follow the file
            while not self._stop.is_set():
                if not self.path.exists():
                    time.sleep(1)
                    continue
                with self.path.open("r", errors="ignore") as f:
                    f.seek(0, os.SEEK_END)
                    while not self._stop.is_set():
                        pos = f.tell()
                        line = f.readline()
                        if not line:
                            time.sleep(0.5)
                            f.seek(pos)
                        else:
                            self.lines.append(line.rstrip())
                            self.lines = self.lines[-(self.max_lines * 2) :]
        except Exception:
            # Keep quiet; UI will just show nothing
            pass

# ---------------- App state & broadcaster ----------------
class Broadcaster:
    def __init__(self):
        self.clients: List[WebSocket] = []
        self.lock = threading.Lock()

    async def add(self, ws: WebSocket):
        await ws.accept()
        with self.lock:
            self.clients.append(ws)

    def remove(self, ws: WebSocket):
        with self.lock:
            if ws in self.clients:
                self.clients.remove(ws)

    async def publish(self, payload: Dict[str, Any]):
        dead: List[WebSocket] = []
        for ws in list(self.clients):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for d in dead:
            self.remove(d)

sense = SenseFacade()
camera = Camera(index=0)
motion = MotionTailer(MOTION_LOG, max_lines=100)
bus = Broadcaster()

# ---------------- FastAPI setup ----------------
app = FastAPI(title="pi_productivity Web UI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------- Assets (written once) ----------------
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>pi_productivity</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <header class="topbar">
    <div class="brand">🐾 pi_productivity</div>
    <div class="clock" id="clock"></div>
  </header>

  <main class="grid">
    <section class="panel corgi-panel">
      <img id="corgi" src="/static/dog.svg" alt="Dog mascot" />
      <div class="mode" id="mode">Mode: ...</div>
    </section>

    <section class="panel measures">
      <h3>Measures</h3>
      <div class="measure"><span>Temp</span><b id="temp">--</b><span>°C</span></div>
      <div class="measure"><span>Humidity</span><b id="hum">--</b><span>%</span></div>
      <div class="measure"><span>Pressure</span><b id="pres">--</b><span>hPa</span></div>
      <div class="availability" id="senseAvail"></div>
    </section>

    <section class="panel camera">
      <h3>Camera</h3>
      <img id="cam" src="/camera.jpg" alt="Camera" />
    </section>

    <section class="panel motion">
      <h3>Motion tasks/events</h3>
      <pre id="motion"></pre>
    </section>
  </main>

  <footer class="foot">Made with FastAPI • Resize window to see compact mode</footer>
  <script src="/static/app.js"></script>
</body>
</html>
"""

APP_JS = """
const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');

function dogUrl(state, activity){
  const mode = encodeURIComponent(state ?? 'idle');
  let act = Number(activity ?? 0);
  if(!Number.isFinite(act)){ act = 0; }
  act = Math.max(0, Math.min(1, act));
  const ts = Date.now();
  return `/dog.svg?mode=${mode}&activity=${act.toFixed(2)}&ts=${ts}`;
}

function tickClock(){
  const now = new Date();
  clock.textContent = now.toLocaleString();
}
setInterval(tickClock, 500);

function setCorgi(state, activity){
  // swap CSS class to animate different states
  const next = (state || 'idle');
  corgi.classList.remove('idle','focus','break','alert');
  corgi.classList.add(next);
  corgi.src = dogUrl(next, activity);
  corgi.dataset.mode = next;
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    const j = await r.json();
    const s = j.sense;
    tempEl.textContent = s.temperature?.toFixed?.(1) ?? '--';
    humEl.textContent = s.humidity?.toFixed?.(1) ?? '--';
    presEl.textContent = s.pressure?.toFixed?.(1) ?? '--';
    senseAvail.textContent = s.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
    motionEl.textContent = (j.motion||[]).slice(-50).join('\n');
    modeEl.textContent = 'Mode: ' + j.mode;

    const state = (j.mode||'IDLE').toLowerCase();
    const activity = j.activity_level ?? 0;
    setCorgi(state, activity);
  }catch(e){
    console.error(e);
  }
}

async function initWS(){
  try{
    const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
    ws.onmessage = (ev)=>{
      const j = JSON.parse(ev.data);
      if(j.kind==='tick'){
        const s = j.payload;
        tempEl.textContent = s.sense.temperature?.toFixed?.(1) ?? '--';
        humEl.textContent = s.sense.humidity?.toFixed?.(1) ?? '--';
        presEl.textContent = s.sense.pressure?.toFixed?.(1) ?? '--';
        senseAvail.textContent = s.sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
        motionEl.textContent = (s.motion||[]).slice(-50).join('\n');
        modeEl.textContent = 'Mode: ' + s.mode;
        const activity = s.activity_level ?? 0;
        setCorgi((s.mode||'IDLE').toLowerCase(), activity);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

refreshOnce();
initWS();
"""

DOG_SVG_FALLBACK = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 320" role="img" aria-label="Dog mascot">
  <rect id="bg" width="320" height="320" rx="28" fill="#0f1720"/>
  <g id="dog" transform="translate(40 60)">
    <g id="ear-left-group" transform="rotate(0 60 40)">
      <path id="ear-left" d="M14 88 Q60 4 106 66 L86 98 Z" fill="#ffd8b3" stroke="#3d2b1f" stroke-width="4"/>
    </g>
    <g id="ear-right-group" transform="translate(120 0) rotate(0 60 40)">
      <path id="ear-right" d="M14 88 Q60 4 106 66 L86 98 Z" fill="#ffd8b3" stroke="#3d2b1f" stroke-width="4"/>
    </g>
    <ellipse id="body" cx="120" cy="160" rx="120" ry="100" fill="#f7b37f" stroke="#3d2b1f" stroke-width="6"/>
    <ellipse id="belly" cx="120" cy="200" rx="82" ry="60" fill="#fff4e6" opacity="0.95"/>
    <g id="tail-group" transform="rotate(-12 0 180)">
      <path id="tail-path" d="M-36 220 Q-60 140 -6 130" fill="none" stroke="#f7b37f" stroke-width="22" stroke-linecap="round"/>
      <circle id="tail-tip" cx="-8" cy="128" r="18" fill="#fff4e6"/>
    </g>
    <ellipse id="eye-left" cx="80" cy="110" rx="20" ry="14" fill="#161616"/>
    <ellipse id="eye-right" cx="160" cy="110" rx="20" ry="14" fill="#161616"/>
    <circle id="eye-highlight-left" cx="72" cy="101.6" r="7" fill="#ffffff" opacity="0.6"/>
    <circle id="eye-highlight-right" cx="152" cy="101.6" r="7" fill="#ffffff" opacity="0.6"/>
    <circle id="cheek-left" cx="70" cy="180" r="20" fill="#ffceb0" opacity="0.5"/>
    <circle id="cheek-right" cx="170" cy="180" r="20" fill="#ffceb0" opacity="0.5"/>
    <rect id="nose" x="92" y="140" width="56" height="26" rx="16" fill="#202020"/>
    <path id="nose-shadow" d="M104 154 Q120 164 136 154" fill="none" stroke="#000000" stroke-width="3" opacity="0.35"/>
    <path id="mouth" d="M70 200 Q120 188 170 200" fill="none" stroke="#3d2b1f" stroke-width="6" stroke-linecap="round"/>
  </g>
  <g id="label" transform="translate(0 0)">
    <rect id="label-rect" x="90" y="18" width="140" height="36" rx="18" fill="#3fa9f5" opacity="0.9"/>
    <text id="label-text" x="160" y="43" font-size="18" text-anchor="middle" font-family="'Nunito','Segoe UI',sans-serif" fill="#04111c">Idle</text>
  </g>
</svg>
"""

try:
    OFFICIAL_DOG_SVG = DOG_SVG_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    OFFICIAL_DOG_SVG = DOG_SVG_FALLBACK

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

STYLES_CSS = """
:root{ --bg:#0b0f14; --panel:#0f1720; --text:#e6edf3; --muted:#9fb0c0; --accent:#3fa9f5; }
*{ box-sizing:border-box; }
html,body{ margin:0; height:100%; background:var(--bg); color:var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Inter, Ubuntu, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji'; }
.topbar{ display:flex; justify-content:space-between; align-items:center; padding:10px 14px; background:#0c131b; position:sticky; top:0; z-index:10; box-shadow:0 2px 8px rgba(0,0,0,.3) }
.brand{ font-weight:700; letter-spacing:.3px }
.clock{ color:var(--muted); font-variant-numeric:tabular-nums }
.grid{ display:grid; grid-template-columns: repeat(12, 1fr); gap:12px; padding:12px; }
.panel{ background:var(--panel); border:1px solid #152033; border-radius:14px; padding:12px; box-shadow:0 6px 20px rgba(0,0,0,.25); }
.corgi-panel{ grid-column: span 4; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.corgi-panel img{ width:100%; max-width:280px; transition: transform .4s ease; filter: drop-shadow(0 10px 25px rgba(0,0,0,.35)); }
.corgi-panel img.idle{ transform: translateY(0px); }
.corgi-panel img.focus{ transform: translateY(-6px) scale(1.02); }
.corgi-panel img.break{ transform: translateY(2px) scale(.98); filter: grayscale(.2) brightness(.9); }
.corgi-panel img.alert{ animation: wiggle .18s ease-in-out 0s 8 alternate; }
@keyframes wiggle{ from{ transform: rotate(-6deg)} to{ transform: rotate(6deg)} }
.corgi-panel .mode{ margin-top:8px; color:var(--muted) }

.measures{ grid-column: span 3; }
.measures h3{ margin:2px 0 10px }
.measure{ display:flex; align-items:baseline; gap:6px; margin:4px 0 }
.measure b{ font-size:1.3rem }
.availability{ margin-top:6px; color:var(--muted) }

.camera{ grid-column: span 5; }
.camera img{ width:100%; border-radius:10px; border:1px solid #1b2940 }

.motion{ grid-column: span 12; }
.motion pre{ white-space: pre-wrap; max-height: 260px; overflow:auto; color:#cfe3ff; background:#0b1220; padding:10px; border-radius:10px; border:1px solid #152033 }

.foot{ text-align:center; color:var(--muted); padding:8px 0 16px }

/* Compact mode: when small, show only corgi + measures */
@media (max-width: 680px){
  .grid{ grid-template-columns: repeat(4, 1fr); }
  .camera{ display:none }
  .motion{ display:none }
  .corgi-panel{ grid-column: span 4; }
  .measures{ grid-column: span 4; }
}
"""

DOG_VARIANTS: Dict[str, Dict[str, Any]] = {
    "idle": {
        "label": "Idle",
        "bg": "#0f1720",
        "body": "#f7b37f",
        "belly": "#fff4e6",
        "ear": "#ffd8b3",
        "mask": "#3d2b1f",
        "cheek": "#ffceb0",
        "cheek_opacity": 0.5,
        "tail": "#f7b37f",
        "tail_tip": "#fff4e6",
        "accent": "#3fa9f5",
        "label_text": "#04111c",
        "highlight": "#ffffff",
        "highlight_opacity": 0.6,
        "tuning": {
            "tail_base": -12,
            "tail_range": 25,
            "ear_tilt": 0,
            "ear_range": 14,
            "eye_y": 110,
            "eye_range": -6,
            "eye_open": 14,
            "eye_open_range": 0,
            "mouth_y": 200,
            "mouth_curve": 188,
            "mouth_range": 6,
            "nose_height": 26,
            "nose_range": 2,
        },
    },
    "focus": {
        "label": "Focus",
        "bg": "#061321",
        "body": "#f5a96a",
        "belly": "#ffe8d1",
        "ear": "#ffcfa1",
        "mask": "#2c1c16",
        "cheek": "#ffbfa3",
        "cheek_opacity": 0.45,
        "tail": "#f5a96a",
        "tail_tip": "#ffe8d1",
        "accent": "#7ec6ff",
        "label_text": "#04111c",
        "highlight": "#ffffff",
        "highlight_opacity": 0.85,
        "tuning": {
            "tail_base": -6,
            "tail_range": 15,
            "ear_tilt": -6,
            "ear_range": 20,
            "eye_y": 108,
            "eye_range": -12,
            "eye_open": 12,
            "eye_open_range": -4,
            "mouth_y": 190,
            "mouth_curve": 178,
            "mouth_range": -10,
            "nose_height": 24,
            "nose_range": -4,
        },
    },
    "break": {
        "label": "Break",
        "bg": "#111b26",
        "body": "#f6c08f",
        "belly": "#fff5e6",
        "ear": "#ffe0b9",
        "mask": "#3b2619",
        "cheek": "#ffc8bf",
        "cheek_opacity": 0.7,
        "tail": "#f6c08f",
        "tail_tip": "#fff5e6",
        "accent": "#ffd86b",
        "label_text": "#1b1208",
        "highlight": "#ffffff",
        "highlight_opacity": 0.5,
        "tuning": {
            "tail_base": -20,
            "tail_range": 32,
            "ear_tilt": 6,
            "ear_range": -8,
            "eye_y": 112,
            "eye_range": 4,
            "eye_open": 16,
            "eye_open_range": 2,
            "mouth_y": 205,
            "mouth_curve": 196,
            "mouth_range": 12,
            "nose_height": 28,
            "nose_range": 4,
        },
    },
    "alert": {
        "label": "Alert",
        "bg": "#1f0a0d",
        "body": "#f09067",
        "belly": "#ffdcd2",
        "ear": "#ffbeaa",
        "mask": "#351312",
        "cheek": "#ff8b8b",
        "cheek_opacity": 0.85,
        "tail": "#f09067",
        "tail_tip": "#ffdcd2",
        "accent": "#ff6b6b",
        "label_text": "#1f0a0d",
        "highlight": "#fff5f5",
        "highlight_opacity": 0.3,
        "tuning": {
            "tail_base": -30,
            "tail_range": 45,
            "ear_tilt": 10,
            "ear_range": -30,
            "eye_y": 106,
            "eye_range": -16,
            "eye_open": 10,
            "eye_open_range": -6,
            "mouth_y": 190,
            "mouth_curve": 170,
            "mouth_range": -18,
            "nose_height": 22,
            "nose_range": -6,
        },
    },
}

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def render_dog_svg(mode: str, activity: float) -> str:
    variant = DOG_VARIANTS.get(mode.lower(), DOG_VARIANTS["idle"])
    tuning = variant["tuning"]
    act = clamp(activity)
    tail_angle = tuning["tail_base"] + tuning["tail_range"] * act
    ear_left = tuning["ear_tilt"] + tuning["ear_range"] * act
    ear_right = -tuning["ear_tilt"] - tuning["ear_range"] * 0.8 * act
    eye_y = tuning["eye_y"] + tuning["eye_range"] * act
    eye_ry = max(6.0, tuning["eye_open"] + tuning["eye_open_range"] * act)
    mouth_y = tuning["mouth_y"]
    mouth_q = tuning["mouth_curve"] + tuning["mouth_range"] * act
    nose_height = max(18.0, tuning["nose_height"] + tuning["nose_range"] * act)
    nose_y = eye_y + 30
    tail_curve_x = -60 + 110 * act
    tail_curve_y = 140 - 80 * act
    eye_highlight = 4 + 3 * (1 - act)
    eye_y_minus = eye_y - (eye_ry * 0.6)
    nose_y_plus = nose_y + nose_height - 12
    nose_y_plus2 = nose_y_plus + 10
    try:
        template = DOG_SVG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        template = OFFICIAL_DOG_SVG

    root = ET.fromstring(template)

    def find(tag: str, element_id: str) -> Optional[ET.Element]:
        return root.find(f".//{{{SVG_NS}}}{tag}[@id='{element_id}']")

    def set_attrs(element: Optional[ET.Element], **attrs: str) -> None:
        if element is None:
            return
        for key, value in attrs.items():
            element.set(key, value)

    set_attrs(find("rect", "bg"), fill=variant["bg"])
    set_attrs(find("ellipse", "body"), fill=variant["body"], stroke=variant["mask"])
    set_attrs(find("ellipse", "belly"), fill=variant["belly"])
    set_attrs(find("path", "ear-left"), fill=variant["ear"], stroke=variant["mask"])
    set_attrs(find("path", "ear-right"), fill=variant["ear"], stroke=variant["mask"])

    left_group = find("g", "ear-left-group")
    if left_group is not None:
        left_group.set("transform", f"rotate({ear_left:.2f} 60 40)")

    right_group = find("g", "ear-right-group")
    if right_group is not None:
        right_group.set("transform", f"translate(120 0) rotate({ear_right:.2f} 60 40)")

    tail_group = find("g", "tail-group")
    if tail_group is not None:
        tail_group.set("transform", f"rotate({tail_angle:.2f} 0 180)")

    set_attrs(
        find("path", "tail-path"),
        d=f"M-36 220 Q{tail_curve_x:.2f} {tail_curve_y:.2f} -6 130",
        stroke=variant["tail"],
    )
    set_attrs(find("circle", "tail-tip"), fill=variant["tail_tip"])

    set_attrs(find("ellipse", "eye-left"), cy=f"{eye_y:.2f}", ry=f"{eye_ry:.2f}")
    set_attrs(find("ellipse", "eye-right"), cy=f"{eye_y:.2f}", ry=f"{eye_ry:.2f}")

    highlight_attrs = {
        "cy": f"{eye_y_minus:.2f}",
        "r": f"{eye_highlight:.2f}",
        "fill": variant["highlight"],
        "opacity": f"{variant['highlight_opacity']:.2f}",
    }
    set_attrs(find("circle", "eye-highlight-left"), **highlight_attrs)
    set_attrs(find("circle", "eye-highlight-right"), **highlight_attrs)

    cheek_attrs = {
        "fill": variant["cheek"],
        "opacity": f"{variant['cheek_opacity']:.2f}",
    }
    set_attrs(find("circle", "cheek-left"), **cheek_attrs)
    set_attrs(find("circle", "cheek-right"), **cheek_attrs)

    set_attrs(find("rect", "nose"), y=f"{nose_y:.2f}", height=f"{nose_height:.2f}")
    set_attrs(
        find("path", "nose-shadow"),
        d=f"M104 {nose_y_plus:.2f} Q120 {nose_y_plus2:.2f} 136 {nose_y_plus:.2f}",
    )
    set_attrs(
        find("path", "mouth"),
        d=f"M70 {mouth_y:.2f} Q120 {mouth_q:.2f} 170 {mouth_y:.2f}",
        stroke=variant["mask"],
    )

    set_attrs(find("rect", "label-rect"), fill=variant["accent"])
    label_text = find("text", "label-text")
    if label_text is not None:
        label_text.text = variant["label"]
        label_text.set("fill", variant["label_text"])

    svg = ET.tostring(root, encoding="unicode")
    if not svg.startswith("<?xml"):
        svg = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + svg
    return svg


PLACEHOLDER_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \" ,#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13\"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf7\xfa(\xa2\x80?\xff\xd9"
)


def _write_asset(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        existing = path.read_bytes() if path.exists() else None
        if existing != content:
            path.write_bytes(content)
    else:
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != content:
            path.write_text(content, encoding="utf-8")


def ensure_web_assets() -> None:
    _write_asset(WEB_DIR / "index.html", INDEX_HTML)
    _write_asset(STATIC_DIR / "app.js", APP_JS)
    _write_asset(STATIC_DIR / "styles.css", STYLES_CSS)
    _write_asset(DOG_SVG_PATH, OFFICIAL_DOG_SVG)


def build_status_payload() -> Dict[str, Any]:
    recent_motion = motion.snapshot()
    window = getattr(motion, "max_lines", 50) or 50
    activity = min(len(recent_motion) / max(1, float(window)), 1.0)
    return {
        "mode": get_current_mode(),
        "sense": sense.readings(),
        "motion": recent_motion,
        "activity_level": round(activity, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


async def broadcast_loop() -> None:
    while True:
        payload = await run_in_threadpool(build_status_payload)
        await bus.publish({"kind": "tick", "payload": payload})
        await asyncio.sleep(2)


@app.get("/", response_class=HTMLResponse)
async def home(_: Request) -> HTMLResponse:
    template = jinja_env.get_template("index.html")
    html = template.render()
    return HTMLResponse(html)


@app.get("/healthz", response_class=JSONResponse)
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "mode": get_current_mode()})


@app.get("/api/status", response_class=JSONResponse)
async def api_status() -> JSONResponse:
    payload = await run_in_threadpool(build_status_payload)
    return JSONResponse(payload)


@app.post("/api/mode", response_class=JSONResponse)
async def api_set_mode(data: Dict[str, Any]) -> JSONResponse:
    mode = data.get("mode")
    if mode is not None:
        set_mode(str(mode))
    return JSONResponse({"mode": get_current_mode()})


@app.get("/camera.jpg")
async def camera_jpeg() -> StreamingResponse:
    frame = await run_in_threadpool(camera.read_jpeg)
    data = frame or PLACEHOLDER_JPEG
    return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")


@app.get("/dog.svg")
async def dog_svg(mode: str = "idle", activity: float = 0.0) -> Response:
    svg = await run_in_threadpool(render_dog_svg, mode, activity)
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await bus.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        bus.remove(ws)
    except Exception:
        bus.remove(ws)


_broadcast_task: Optional[asyncio.Task] = None


@app.on_event("startup")
async def on_startup() -> None:
    global _broadcast_task
    ensure_web_assets()
    if not motion.thread.is_alive():
        motion.start()
    _broadcast_task = asyncio.create_task(broadcast_loop())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global _broadcast_task
    motion.stop()
    if _broadcast_task:
        _broadcast_task.cancel()
        with suppress(asyncio.CancelledError):
            await _broadcast_task
        _broadcast_task = None


def start_in_background(host: str = HOST, port: int = PORT) -> threading.Thread:
    """Launch the FastAPI server in a background thread using uvicorn."""

    def _run() -> None:
        import uvicorn

        uvicorn.run(app, host=host, port=port, log_level="info")

    thread = threading.Thread(target=_run, name="webapp-server", daemon=True)
    thread.start()
    return thread


def run() -> None:
    """Run the web app in the foreground."""

    ensure_web_assets()
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    run()

