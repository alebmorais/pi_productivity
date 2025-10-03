"""
main.py — pi_productivity

Adds a FastAPI-based web app that runs alongside your existing pipeline.
- Mostra diagnósticos do Sense HAT (ou valores simulados quando não houver hardware)
- Exibe o modo atual e permite trocar manualmente via presets na interface
- Mostra a câmera (captura ao vivo ou fallback do arquivo last_posture.jpg)
- Resume ajustes de postura e tarefas Motion lendo os CSVs em ~/pi_productivity/logs
- Lê eventos recentes do Motion tentando detectar automaticamente o caminho do log

How it works
------------
• On startup, este arquivo também gera os assets básicos em ./web/ (index.html, app.js, styles.css) caso não existam.
• The web app runs on 0.0.0.0 (LAN-accessible) at port 8090 by default (override via env WEBAPP_PORT).
• The server runs in a background thread so your other tasks can continue to run.
• Em telas pequenas a UI reorganiza os cartões para caber em uma única coluna.

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
import csv
import math
import os
import io
try:
    import cv2  # type: ignore
except Exception:  # noqa: BLE001
    cv2 = None  # type: ignore
import json
import time
import enum
import threading
from collections import deque
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Iterable

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
PORT = int(os.getenv("WEBAPP_PORT", "8090"))
HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")

_DEFAULT_PROJECT_ROOT = Path.home() / "pi_productivity"
PROJECT_ROOT = Path(os.getenv("PI_PRODUCTIVITY_DIR", str(_DEFAULT_PROJECT_ROOT))).expanduser()
LOG_DIR = Path(os.getenv("PI_PRODUCTIVITY_LOG_DIR", str(PROJECT_ROOT / "logs"))).expanduser()
POSTURE_CSV = Path(os.getenv("PI_PRODUCTIVITY_POSTURE_CSV", str(LOG_DIR / "posture_events.csv"))).expanduser()
TASK_CSV = Path(os.getenv("PI_PRODUCTIVITY_TASK_CSV", str(LOG_DIR / "task_events.csv"))).expanduser()
LAST_POSTURE_JPEG = Path(os.getenv("PI_PRODUCTIVITY_POSTURE_JPEG", str(PROJECT_ROOT / "last_posture.jpg"))).expanduser()

_motion_env = os.getenv("MOTION_LOG_PATH", "").strip()
_motion_candidates: List[Path] = []
if _motion_env:
    _motion_candidates.append(Path(_motion_env).expanduser())
_motion_candidates.append(LOG_DIR / "motion.log")
_motion_candidates.append(Path("/var/log/motion/motion.log"))

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
        if cv2 is None:
            self.cap = None
            return
        try:
            self.cap = cv2.VideoCapture(self.index)
            if not self.cap or not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None

    def read_jpeg(self) -> Optional[bytes]:
        if cv2 is not None:
            with self.lock:
                if not self.cap:
                    self._open()
                if self.cap:
                    ok, frame = self.cap.read()
                    if ok:
                        ok, buf = cv2.imencode(".jpg", frame)
                        if ok:
                            return bytes(buf)
        return self._read_snapshot()

    def _read_snapshot(self) -> Optional[bytes]:
        candidates = [LAST_POSTURE_JPEG, PROJECT_ROOT / "last_posture.jpg"]
        for path in candidates:
            if path and path.exists():
                try:
                    return path.read_bytes()
                except Exception:
                    continue
        return None

# ---------------- Motion log tail ----------------
class MotionTailer:
    def __init__(self, paths: Iterable[Path], max_lines: int = 50):
        candidates = [Path(p) for p in paths if str(p)]
        if not candidates:
            candidates = [Path("/var/log/motion/motion.log")]
        self.paths = candidates
        self.current_path: Optional[Path] = None
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

    def _resolve_path(self) -> Optional[Path]:
        for candidate in self.paths:
            if candidate.exists():
                return candidate
        return self.paths[0] if self.paths else None

    def _run(self):
        try:
            while not self._stop.is_set():
                path = self._resolve_path()
                if not path or not path.exists():
                    self.current_path = path
                    time.sleep(1)
                    continue
                self.current_path = path
                try:
                    with path.open("r", errors="ignore") as f:
                        if not self.lines:
                            self.lines = f.readlines()[-self.max_lines :]
                        f.seek(0, os.SEEK_END)
                        while not self._stop.is_set():
                            pos = f.tell()
                            line = f.readline()
                            if not line:
                                time.sleep(0.5)
                                f.seek(pos)
                                if path != self._resolve_path():
                                    break
                            else:
                                self.lines.append(line.rstrip())
                                self.lines = self.lines[-(self.max_lines * 2) :]
                except Exception:
                    time.sleep(1)
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
motion = MotionTailer(_motion_candidates, max_lines=100)
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
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>pi_productivity</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <header class="topbar">
    <div class="brand">pi_productivity</div>
    <div class="mode-pill" id="mode">Modo: ...</div>
    <div class="clock" id="clock"></div>
  </header>

  <main class="grid">
    <section class="panel mode-panel">
      <h3>Presets de modo</h3>
      <p class="preset-hint">Troque o modo manualmente quando não estiver usando o joystick.</p>
      <div class="preset-list">
        <button type="button" class="preset-btn" data-mode-btn data-mode="idle">Idle</button>
        <button type="button" class="preset-btn" data-mode-btn data-mode="focus">Focus</button>
        <button type="button" class="preset-btn" data-mode-btn data-mode="break">Break</button>
        <button type="button" class="preset-btn" data-mode-btn data-mode="alert">Alert</button>
      </div>
      <div class="preset-status" id="presetStatus"></div>
    </section>

    <section class="panel measures">
      <h3>Sense HAT</h3>
      <div class="measure"><span>Temp</span><b id="temp">--</b><span>°C</span></div>
      <div class="measure"><span>Umid.</span><b id="hum">--</b><span>%</span></div>
      <div class="measure"><span>Press.</span><b id="pres">--</b><span>hPa</span></div>
      <div class="availability" id="senseAvail"></div>
    </section>
    </section>

    <section class="panel camera">
      <h3>Última captura</h3>
      <img id="cam" src="/camera.jpg" alt="Última captura da câmera" />
    </section>

    <section class="panel tasks">
      <h3>Tarefas Motion</h3>
      <div class="stats-row">
        <div class="stat">
          <span>Total</span>
          <b id="tasksTotal">0</b>
        </div>
        <div class="stat">
          <span>Concluídas</span>
          <b id="tasksCompleted">0</b>
        </div>
        <div class="stat">
          <span>Criadas</span>
          <b id="tasksCreated">0</b>
        </div>
      </div>
      <ul class="event-list" id="tasksRecent"></ul>
    </section>

    <section class="panel motion">
      <h3>Log do Motion</h3>
      <div class="motion-source" id="motionSource"></div>
      <pre id="motion"></pre>
    </section>
  </main>

  <footer class="foot">Feito com FastAPI • Atualiza automaticamente a cada poucos segundos</footer>
  <script src="/static/app.js"></script>
</body>
</html>
"""

APP_JS = """const clock = document.getElementById('clock');
const modeEl = document.getElementById('mode');
const presetButtons = Array.from(document.querySelectorAll('[data-mode-btn]'));
const presetStatus = document.getElementById('presetStatus');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const postureEventsEl = document.getElementById('postureEvents');
const postureAdjustEl = document.getElementById('postureAdjust');
const postureListEl = document.getElementById('postureRecent');
const tasksTotalEl = document.getElementById('tasksTotal');
const tasksCompletedEl = document.getElementById('tasksCompleted');
const tasksCreatedEl = document.getElementById('tasksCreated');
const tasksListEl = document.getElementById('tasksRecent');
const motionEl = document.getElementById('motion');
const VALID_MODES = ['idle', 'focus', 'break', 'alert'];

function isPresent(value){
  return value !== undefined && value !== null;
}

function ensureObject(value){
  return value !== undefined && value !== null && typeof value === 'object' ? value : {};
}

function ensureArray(value){
  return Array.isArray(value) ? value : [];
}

function hasOwn(obj, prop){
  return Object.prototype.hasOwnProperty.call(obj, prop);
}

function normalizeMode(value){
  if(!isPresent(value)){
    return 'idle';
  }
  const lower = String(value).toLowerCase();
  for(const candidate of VALID_MODES){
    if(lower.includes(candidate)){
      return candidate;
    }
  }
  return 'idle';
}

function describeMode(value){
  const normalized = normalizeMode(value);
  return {
    normalized,

  };
}

function formatNumber(value){
  const num = Number(value);
  if(!Number.isFinite(num)){
    return '--';
  }
  return num.toFixed(1);
}

function formatInt(value){
  const num = Number.parseInt(value, 10);
  if(!Number.isFinite(num)){
    return '0';
  }
  return String(num);
}

function formatTimestamp(value){
  if(!value){
    return '—';
  }
  const parsed = new Date(value);
  if(Number.isNaN(parsed.getTime())){
    return String(value);
  }
  return parsed.toLocaleString();
}

function tickClock(){
  const now = new Date();
  clock.textContent = now.toLocaleString();
}

function setPresetStatus(message = '', isError = false){
  if(!presetStatus){
    return;
  }
  presetStatus.textContent = message;
  presetStatus.classList.toggle('error', Boolean(isError));
}

function updatePresetButtons(activeMode){
  if(!presetButtons.length){
    return;
  }
  const normalized = normalizeMode(activeMode);
  for(const btn of presetButtons){
    const target = normalizeMode(btn.dataset.mode);
    const isActive = target === normalized;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  }
}

function bindPresetButtons(){
  if(!presetButtons.length){
    return;
  }
  for(const btn of presetButtons){
    btn.addEventListener('click', async ()=>{
      const desiredInfo = describeMode(btn.dataset.mode);
      setPresetStatus(`Atualizando para ${desiredInfo.label}...`);
      btn.disabled = true;
      try{
        const response = await fetch('/api/mode', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({mode: desiredInfo.normalized})
        });
        if(!response.ok){
          throw new Error(`HTTP ${response.status}`);
        }
        let payload = {};
        try{
          payload = await response.json();
        }catch(_err){
          payload = {};
        }
        const next = updateModeDisplay(payload.mode ?? desiredInfo.normalized);
        updatePresetButtons(next);
        const nextLabel = describeMode(next).label;
        setPresetStatus(`Modo definido para ${nextLabel}.`);
      }catch(err){
        console.error('Failed to set mode', err);
        setPresetStatus('Não foi possível atualizar o modo agora.', true);
      }finally{
        btn.disabled = false;
      }
    });
  }
}

function updateModeDisplay(modeValue){
  const info = describeMode(modeValue);
  if(modeEl){
    modeEl.textContent = `Modo: ${info.label}`;
  }
  return info.normalized;
}

function setPresetStatus(message = '', isError = false){
  if(!presetStatus){
    return;
  }
  presetStatus.textContent = message;
  if(isError){
    presetStatus.classList.add('error');
  }else{
    presetStatus.classList.remove('error');
  }
}

function updatePresetButtons(activeMode){
  if(!presetButtons.length){
    return;
  }
  const normalized = normalizeMode(activeMode);
  for(const btn of presetButtons){
    const target = normalizeMode(btn.dataset.mode);
    const isActive = target === normalized;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  }
}

function bindPresetButtons(){
  if(!presetButtons.length){
    return;
  }
  for(const btn of presetButtons){
    btn.addEventListener('click', async ()=>{
      const desiredInfo = describeMode(btn.dataset.mode);
      setPresetStatus(`Atualizando para ${desiredInfo.label}...`);
      btn.disabled = true;
      try{
        const response = await fetch('/api/mode', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({mode: desiredInfo.normalized})
        });
        if(!response.ok){
          throw new Error(`HTTP ${response.status}`);
        }
        let payload = {};
        try{
          payload = await response.json();
        }catch(_err){
          payload = {};
        }
        const next = updateModeDisplay(payload.mode ?? desiredInfo.normalized);
        setCorgi(next, 0);
        updatePresetButtons(next);
        const nextLabel = describeMode(next).label;
        setPresetStatus(`Modo definido para ${nextLabel}.`);
      }catch(err){
        console.error('Failed to set mode', err);
        setPresetStatus('Não foi possível atualizar o modo agora.', true);
      }finally{
        btn.disabled = false;
      }
    });
  }
}

function updateSense(senseData){
  const sense = ensureObject(senseData);
  tempEl.textContent = formatNumber(sense.temperature);
  humEl.textContent = formatNumber(sense.humidity);
  presEl.textContent = formatNumber(sense.pressure);

  if(sense.available){
    senseAvail.textContent = 'Sense HAT disponível';
  }else if(hasOwn(sense, 'error') && isPresent(sense.error)){
    senseAvail.textContent = String(sense.error);
  }else{
    senseAvail.textContent = 'Sense HAT indisponível';
  }
}

function renderList(element, items, fallbackText, decorate){
  if(!element){
    return;
  }
  element.textContent = '';
  if(!items.length){
    const li = document.createElement('li');
    li.className = 'event-item empty';
    li.textContent = fallbackText;
    element.appendChild(li);
    return;
  }
  for(const item of items){
    const li = document.createElement('li');
    li.className = 'event-item';
    decorate(li, item);
    element.appendChild(li);
  }
}

function updatePosture(data){
  const info = ensureObject(data);
  postureEventsEl.textContent = formatInt(info.total_events);
  postureAdjustEl.textContent = formatInt(info.adjustments);
  const items = ensureArray(info.recent);
  renderList(postureListEl, items, 'Nenhum evento recente.', (li, entry)=>{
    const ok = Boolean(entry && entry.ok);
    const ts = formatTimestamp(entry && entry.timestamp);
    const reason = entry && entry.reason ? ` · ${entry.reason}` : '';
    const tilt = entry && Number.isFinite(Number(entry.tilt)) ? ` · tilt ${Number(entry.tilt).toFixed(1)}°` : '';
    const nod = entry && Number.isFinite(Number(entry.nod)) ? ` · nod ${Number(entry.nod).toFixed(1)}°` : '';
    li.textContent = `${ts} • ${ok ? 'OK' : 'Ajuste'}${reason}${tilt}${nod}`;
    if(!ok){
      li.classList.add('warn');
    }
  });
}

function updateTasks(data){
  const info = ensureObject(data);
  tasksTotalEl.textContent = formatInt(info.total_events);
  tasksCompletedEl.textContent = formatInt(info.completed);
  tasksCreatedEl.textContent = formatInt(info.created);
  const items = ensureArray(info.recent);
  renderList(tasksListEl, items, 'Nenhum evento recente.', (li, entry)=>{
    const ts = formatTimestamp(entry && entry.timestamp);
    const action = entry && entry.action ? String(entry.action).toUpperCase() : 'EVENTO';
    const section = entry && entry.section_title ? ` · ${entry.section_title}` : '';
    const name = entry && entry.task_name ? ` — ${entry.task_name}` : '';
    li.textContent = `${ts} • ${action}${section}${name}`;
  });
}

function updateMotion(lines, source){
  const list = ensureArray(lines).map((item)=>String(item));
  motionEl.textContent = list.length ? list.join('\n') : 'Nenhum evento recente do Motion.';
  if(motionSourceEl){
    motionSourceEl.textContent = source ? `Fonte: ${source}` : '';
  }
}
}

function applyStatus(payload){
  if(!payload || typeof payload !== 'object'){
    return;
  }
  const normalizedMode = updateModeDisplay(payload.mode);
  updatePresetButtons(normalizedMode);
  updateSense(payload.sense);
  updatePosture(payload.posture);
  updateTasks(payload.tasks);
  updateMotion(payload.motion, payload.motion_source);
  refreshCamera();
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    if(!r.ok){
      console.error('Status fetch failed', r.status, r.statusText);
      return;
    }
    const j = await r.json();
    applyStatus(j);
  }catch(err){
    console.error('Initial refresh failed', err);
  }
}

function handleEnvelope(message){
  if(!message){
    return;
  }
  if(hasOwn(message, 'kind') && message.kind === 'tick'){
    applyStatus(message.payload);
    return;
  }
  if(hasOwn(message, 'mode') || hasOwn(message, 'sense') || hasOwn(message, 'motion')){
    applyStatus(message);
  }
}

async function initWS(){
  try{
    const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
    ws.onmessage = (ev)=>{
      try{
        const message = JSON.parse(ev.data);
        handleEnvelope(message);
      }catch(err){
        console.error('Failed to parse WS message', err);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

updatePresetButtons('idle');
setPresetStatus('');
bindPresetButtons();

tickClock();
setInterval(tickClock, 500);
refreshOnce();
initWS();
"""

STYLES_CSS = """:root{
  --bg:#0b0f14;
  --panel:#0f1720;
  --text:#e6edf3;
  --muted:#9fb0c0;
  --accent:#3fa9f5;
  --warn:#ff9a9a;
}

*{ box-sizing:border-box; }
.preset-btn:hover{ background:rgba(63,169,245,0.12); border-color:var(--accent); transform:translateY(-1px); }
.preset-btn:active{ transform:translateY(0); }
.preset-btn.active{ background:var(--accent); color:#071019; border-color:var(--accent); box-shadow:0 6px 16px rgba(63,169,245,0.35); }
.preset-btn:disabled{ opacity:.55; cursor:not-allowed; }
.preset-status{ min-height:1.2em; font-size:.85rem; color:var(--muted); }
}

@media (max-width: 720px){
  .topbar{ grid-template-columns:1fr; text-align:center; }
  .mode-pill{ justify-self:center; }
  .clock{ justify-self:center; }
  .grid{ grid-template-columns:repeat(4, 1fr); padding:12px; }
  .mode-panel{ grid-column:span 4; }
  .measures{ grid-column:span 4; }
  .posture{ grid-column:span 4; }
  .camera{ grid-column:span 4; }
  .tasks{ grid-column:span 4; }
  .motion{ grid-column:span 4; }
  .preset-btn{ flex:1 1 100%; }
}
"""

def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "ok"}


def _coerce_float(value: Any) -> Optional[float]:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return num


def _coerce_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _tail_csv(path: Path, limit: int) -> deque[Dict[str, Any]]:
    rows: deque[Dict[str, Any]] = deque(maxlen=limit)
    if not path.exists():
        return rows
    try:
        with path.open('r', encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(row)
    except Exception:
        return rows
    return rows


def read_posture_summary(limit: int = 12) -> Dict[str, Any]:
    rows = _tail_csv(POSTURE_CSV, limit)
    total = 0
    adjustments = 0
    recent: List[Dict[str, Any]] = []
    for row in rows:
        ok = _coerce_bool(row.get('ok'))
        total += 1
        if not ok:
            adjustments += 1
        recent.append({
            'timestamp': row.get('timestamp') or '',
            'ok': ok,
            'reason': row.get('reason') or '',
            'tilt': _coerce_float(row.get('tilt_deg')),
            'nod': _coerce_float(row.get('nod_deg')),
            'session_adjustments': _coerce_int(row.get('session_adjustments')),
            'tasks_completed_today': _coerce_int(row.get('tasks_completed_today')),
        })
    return {
        'total_events': total,
        'adjustments': adjustments,
        'recent': recent[-limit:],
        'source': str(POSTURE_CSV) if POSTURE_CSV.exists() else None,
    }


def read_task_summary(limit: int = 12) -> Dict[str, Any]:
    rows = _tail_csv(TASK_CSV, limit)
    total = 0
    completed = 0
    created = 0
    recent: List[Dict[str, Any]] = []
    for row in rows:
        action = (row.get('action') or '').strip().lower()
        total += 1
        if action == 'complete':
            completed += 1
        elif action == 'create':
            created += 1
        recent.append({
            'timestamp': row.get('timestamp') or '',
            'action': action or row.get('action') or '',
            'section_title': row.get('section_title') or '',
            'task_name': row.get('task_name') or row.get('name') or '',
        })
    return {
        'total_events': total,
        'completed': completed,
        'created': created,
        'recent': recent[-limit:],
        'source': str(TASK_CSV) if TASK_CSV.exists() else None,
    }


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


def build_status_payload() -> Dict[str, Any]:
    recent_motion = motion.snapshot()
    if not recent_motion:
        candidate: Optional[Path] = getattr(motion, "current_path", None)
        if candidate is None:
            for path in getattr(motion, "paths", []):
                if path:
                    candidate = path
                    break
        if candidate and not candidate.exists():
            recent_motion = [f"Motion log não encontrado em {candidate}."]
    window = getattr(motion, "max_lines", 50) or 50
    activity = min(len(recent_motion) / max(1, float(window)), 1.0)
    return {
        "mode": get_current_mode(),
        "sense": sense.readings(),
        "motion": recent_motion,
        "activity_level": round(activity, 2),
        "posture": read_posture_summary(),
        "tasks": read_task_summary(),
        "motion_source": str(motion.current_path) if getattr(motion, "current_path", None) else None,
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

