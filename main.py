import os
import csv
import uuid
import io
import threading
import asyncio
import json
import time
import logging
from datetime import datetime
from contextlib import suppress
from pathlib import Path
from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
    Form,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from starlette.concurrency import run_in_threadpool
import uvicorn

import sense_mode
from task_database import TaskDatabase
from motion_client import MotionClient
from ocr_notes import OCRNotes, OCRConfig
from epaper import EPD
from camera_posture import PostureMonitor, PostureConfig

# --- Configuration Loading ---
BASE_DIR = Path(os.getenv("PI_PRODUCTIVITY_DIR", "~/pi_productivity")).expanduser()
load_dotenv(BASE_DIR / ".env")

LOG_DIR = BASE_DIR / "logs"
STATIC_DIR = Path(__file__).parent / "static"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(),
    ],
)

# --- Constants and Settings ---
POSTURE_CSV = LOG_DIR / "posture_events.csv"
TASK_CSV = LOG_DIR / "task_events.csv"
LAST_POSTURE_JPEG = BASE_DIR / "last_posture.jpg"

# Load from environment or set defaults
MOTION_ENABLE_OCR = os.getenv("MOTION_ENABLE_OCR", "1") == "1"
OCR_DEFAULT_DUE_DAYS = int(os.getenv("OCR_DEFAULT_DUE_DAYS", "2"))
MOTION_SYNC_INTERVAL = int(os.getenv("MOTION_SYNC_INTERVAL", "900"))
POSTURE_INTERVAL = int(os.getenv("POSTURE_INTERVAL", "300"))
OCR_INTERVAL = int(os.getenv("OCR_INTERVAL", "600"))
API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key")


async def get_api_key(api_key: str = Depends(api_key_header)):
    if not API_KEY or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


try:
    import cv2
except ImportError:
    cv2 = None
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

# --- Main Application Class ---
class PiProductivity:
    def __init__(self):
        # Hardware and Service Clients
        self.db = TaskDatabase()
        self.motion_client = MotionClient()
        self.ocr_notes = OCRNotes(OCRConfig())
        self.epaper_display = EPD()
        self.posture = PostureMonitor(PostureConfig())
        self.camera = self._init_camera()
        self._cam_lock = threading.Lock()

        # Sense HAT Mode Management
        self.sense_modes = {
            "teleneuro": sense_mode.TeleNeuroMode(),
            "telec": sense_mode.TeleCMode(),
            "study_adhd": sense_mode.StudyADHDMode(),
            "leisure": sense_mode.LeisureMode(),
        }
        self.active_mode = None
        self.active_mode_name = "none"
        
        # Adiciona os modos especiais que não são baseados em timer
        self.MODES = ["posture_check", "ocr_capture"] + list(self.sense_modes.keys())
        self.mode_index = 0

        # State
        self._last_motion_sync = 0
        self._last_posture_check = 0
        self.posture_adjust_count = 0
        self.tasks_completed_today = 0

    def _init_camera(self):
        if not Picamera2:
            logging.warning("Picamera2 not found. Camera functionality disabled.")
            return None
        try:
            cam = Picamera2()
            # Reduzir a resolução pode acelerar a captura e o processamento
            config = cam.create_still_configuration(main={"size": (1024, 576)})
            cam.configure(config)
            cam.start()
            time.sleep(1)  # Allow camera to warm up
            logging.info("Camera initialized.")
            return cam
        except Exception as e:
            logging.error(f"Error initializing camera: {e}", exc_info=True)
            return None

    # --- Mode Management ---
    def stop_current_mode(self):
        if self.active_mode and self.active_mode.is_running():
            self.active_mode.stop()
            logging.info(f"Stopped Sense HAT mode: {self.active_mode_name}")
        self.active_mode = None
        self.active_mode_name = "none"


    # --- Logging ---
    def log_event(self, file_path, fieldnames, event_data):
        file_exists = os.path.isfile(file_path)
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(event_data)

    def log_task_event(self, action, task_name="", section_title=""):
        fieldnames = ["timestamp", "action", "task", "section_title"]
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "task": task_name,
            "section_title": section_title,
        }
        self.log_event(TASK_CSV, fieldnames, event)
        logging.info(f"Logged task event: action={action}, task={task_name}")

    def _log_posture_csv(self, status):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            ts,
            1 if status.get("ok") else 0,
            status.get("reason") or "",
            f"{status.get('tilt',0):.1f}",
            f"{status.get('nod',0):.1f}",
            self.posture_adjust_count,
            self.tasks_completed_today,
        ]
        self.log_event(POSTURE_CSV, ["timestamp", "ok", "reason", "tilt_deg", "nod_deg", "session_adjustments", "tasks_completed_today"], dict(zip(["timestamp", "ok", "reason", "tilt_deg", "nod_deg", "session_adjustments", "tasks_completed_today"], row)))


    # --- Core Logic Methods ---
    def capture_array(self):
        if not self.camera:
            return None
        with self._cam_lock:
            return self.camera.capture_array()

    def read_jpeg(self) -> bytes | None:
        frame = self.capture_array()
        if frame is not None and cv2:
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                with open(LAST_POSTURE_JPEG, "wb") as f:
                    f.write(buf)
                return bytes(buf)
        if LAST_POSTURE_JPEG.exists():
            return LAST_POSTURE_JPEG.read_bytes()
        return None

    def run_posture_once(self):
        frame = self.capture_array()
        if frame is None:
            raise ValueError("Failed to capture frame from camera.")
        
        status = self.posture.analyze_frame(frame)
        self._log_posture_csv(status)
        
        if not status.get("ok"):
            self.posture_adjust_count += 1
            sense_mode.sense.show_letter("!", back_colour=sense_mode.RED)
        else:
            sense_mode.sense.show_letter("✓", back_colour=sense_mode.GREEN)
        time.sleep(1)
        self._render_mode_banner()
        return status

    def run_ocr_once(self):
        frame = self.capture_array()
        if frame is None:
            raise ValueError("Failed to capture frame from camera.")
            
        img_path, txt_path, text = self.ocr_notes.capture_and_ocr(frame)
        
        if MOTION_ENABLE_OCR and self.motion_client and text:
            try:
                self._ocr_apply_to_motion(text)
            except Exception as e:
                logging.error(f"[OCR->Motion] Error: {e}", exc_info=True)

        sense_mode.sense.show_letter("T", back_colour=sense_mode.BLUE)
        time.sleep(1)
        self._render_mode_banner()
        return img_path, txt_path, text

    def _ocr_apply_to_motion(self, text):
        # (This logic remains complex and specific, keeping it encapsulated)
        # ... (previous _ocr_parse_actions and _iso_from_due_hint logic can be moved here or kept as helpers)
        pass # Placeholder for the detailed parsing and API calls

    def maybe_poll_motion(self):
        if not self.motion_client or not self.motion_client.api_key:
            return

        now = time.time()
        if now - self._last_motion_sync < MOTION_SYNC_INTERVAL:
            return

        self._last_motion_sync = now
        try:
            logging.info("[Motion] Starting task sync...")
            tasks = self.motion_client.list_all_tasks_simple()
            synced = self.db.upsert_motion_tasks(tasks)
            logging.info(f"[Motion] Synced {synced} tasks.")

            if self.epaper_display:
                items = self.db.fetch_items_for_display()
                self.epaper_display.render_list(items, title="Pending Tasks")
                logging.info("[E-Paper] Display updated with latest tasks.")

        except Exception as e:
            logging.error(f"[Motion Sync] Error: {e}", exc_info=True)

    # --- UI and Hardware Interaction ---
    def _render_mode_banner(self):
        """Provides immediate visual feedback on the Sense HAT for the current mode."""
        name = self.active_mode_name
        logging.info(f"[Sense] Displaying banner for mode: {name}")

        color = sense_mode.BLUE
        letter = "?"

        if name == "posture_check":
            letter = "P"
            color = [0, 0, 200] # Dark Blue
        elif name == "ocr_capture":
            letter = "O"
            color = [0, 200, 0] # Dark Green
        elif name == "teleneuro":
            letter = "H"
            color = sense_mode.GREEN
        elif name == "telec":
            letter = "C"
            color = sense_mode.BLUE
        elif name == "study_adhd":
            letter = "S"
            color = [200, 100, 0] # Orange
        elif name == "leisure":
            letter = "L"
            color = [150, 0, 200] # Purple
        
        if letter != "?":
            sense_mode.sense.show_letter(letter, back_colour=color)
        else:
            sense_mode.sense.clear()

    def _update_epaper_display(self, mode_name):
        if not self.epaper_display:
            return
        # ... (epaper rendering logic) ...
        pass

    def set_sense_mode(self, mode_name: str):
        """Stops the current mode, sets the new one, and provides feedback."""
        self.stop_current_mode()
        self.active_mode_name = mode_name
        
        # Always show banner for immediate feedback
        self._render_mode_banner()
        time.sleep(0.5) # Give user time to see the banner

        # If it's a timer-based mode, start its thread.
        # Its animation will overwrite the banner, which is expected.
        if mode_name in self.sense_modes:
            self.active_mode = self.sense_modes[mode_name]
            self.active_mode.start()
            logging.info(f"Started active Sense HAT mode: {mode_name}")
        else:
            logging.info(f"Set passive Sense HAT mode: {mode_name}")

        return self.active_mode_name

    def handle_joystick(self, event):
        if event.action != "pressed":
            return

        # Navigation changes the mode
        delta = 0
        if event.direction in ("right", "up"):
            delta = 1
        elif event.direction in ("left", "down"):
            delta = -1
        
        if delta != 0:
            self.mode_index = (self.mode_index + delta) % len(self.MODES)
            new_mode_name = self.MODES[self.mode_index]
            logging.info(f"Joystick changing mode to: {new_mode_name}")
            self.set_sense_mode(new_mode_name)
            return

        # Middle button triggers the action for the CURRENT mode
        if event.direction == "middle":
            current_mode_name = self.active_mode_name
            logging.info(
                f"Joystick middle press detected. Action for mode: {current_mode_name}"
            )
            if "posture" in current_mode_name:
                sense_mode.sense.clear([255, 255, 0])  # Yellow flash
                run_in_threadpool(self.run_posture_once)
                logging.info("Triggered posture check from joystick.")
            elif "ocr" in current_mode_name:
                sense_mode.sense.clear([255, 255, 0])  # Yellow flash
                run_in_threadpool(self.run_ocr_once)
                logging.info("Triggered OCR from joystick.")
            return

    def run_forever(self):
        logging.info("Starting background hardware loop...")
        # Ensure joystick handler is set
        if hasattr(sense_mode.sense, "stick"):
            sense_mode.sense.stick.direction_any = self.handle_joystick
        
        # Set initial mode
        self.set_sense_mode(self.MODES[self.mode_index])
        
        while True:
            now = time.time()
            try:
                self.maybe_poll_motion()

                # Periodic posture check
                if (now - self._last_posture_check) > POSTURE_INTERVAL:
                    self._last_posture_check = now
                    logging.info("Running periodic posture check...")
                    # Run in a thread to avoid blocking the loop
                    threading.Thread(target=self.run_posture_once, daemon=True).start()

            except Exception as e:
                logging.error(f"Error in background loop: {e}", exc_info=True)
            
            time.sleep(15)

# --- FastAPI Setup ---
app = FastAPI(title="pi_productivity Web UI")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Global Instance (created at startup to avoid hardware init during import) ---
sense = None

# 1. Define the Broadcaster class
class Broadcaster:
    def __init__(self):
        self.clients: list[WebSocket] = []
        self.lock = threading.Lock()

    async def add(self, ws: WebSocket):
        await ws.accept()
        with self.lock:
            self.clients.append(ws)

    def remove(self, ws: WebSocket):
        with self.lock:
            if ws in self.clients:
                self.clients.remove(ws)

    async def publish(self, payload: dict):
        dead: list[WebSocket] = []
        for ws in self.clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.remove(d)

# 2. Create a global instance of the Broadcaster
bus = Broadcaster()

# --- API Data Providers ---
def get_sense_readings():
    try:
        return {
            "temperature": round(sense_mode.sense.get_temperature(), 1),
            "humidity": round(sense_mode.sense.get_humidity(), 1),
            "pressure": round(sense_mode.sense.get_pressure(), 1),
            "available": not isinstance(sense_mode.sense, sense_mode.MockSenseHat),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}

def build_status_payload() -> dict:
    return {
        "mode": sense.active_mode_name,
        "sense": get_sense_readings(),
        "tasks": sense.db.fetch_items_for_display(limit=20),
        "timestamp": datetime.utcnow().isoformat(),
    }

# --- Web Application Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sense_modes": sense.sense_modes.keys(),
        "active_mode": sense.active_mode_name
    })

@app.post("/sense/mode", response_class=JSONResponse)
async def set_sense_mode_endpoint(
    mode_name: str = Form(...), api_key: str = Depends(get_api_key)
):
    new_mode = await run_in_threadpool(sense.set_sense_mode, mode_name)
    return JSONResponse({"status": "success", "mode": new_mode})

@app.post("/ocr", response_class=JSONResponse)
async def run_ocr_endpoint(api_key: str = Depends(get_api_key)):
    try:
        img_path, txt_path, text = await run_in_threadpool(sense.run_ocr_once)
        return JSONResponse({"status": "success", "image_path": img_path, "text_path": txt_path, "text": text})
    except Exception as e:
        logging.error("Error in OCR endpoint", exc_info=True)

        # 2. (SEGURO) Envia uma mensagem genérica para o usuário
        # O usuário/invasor não vê nenhuma informação sensível.
        return JSONResponse(
            {"status": "error", "message": "Ocorreu um erro interno ao processar a imagem."},
            status_code=500,
        )
@app.get("/camera.jpg")
async def camera_jpeg(api_key: str = Depends(get_api_key)):
    frame = await run_in_threadpool(sense.read_jpeg)
    data = frame or b''  # Return empty bytes if no frame
    return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")

@app.get("/api/week-calendar", response_class=JSONResponse)
async def get_week_calendar(api_key: str = Depends(get_api_key)):
    """Return tasks grouped by day for the current week."""
    if sense is None:
        return JSONResponse({"error": "Service unavailable"}, status_code=503)
    calendar_data = await run_in_threadpool(sense.db.fetch_week_calendar)
    return JSONResponse(calendar_data)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await bus.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        bus.remove(ws)

# --- FastAPI Lifecycle & Background Tasks ---
async def broadcast_loop():
    while True:
        payload = await run_in_threadpool(build_status_payload)
        await bus.publish({"kind": "tick", "payload": payload})
        await asyncio.sleep(2)

@app.on_event("startup")
async def on_startup():
    # Instantiate the main application object here so hardware initialization
    # (camera, e-paper, GPIO) happens during FastAPI startup where failures
    # can be handled without breaking module import.
    global sense
    if sense is None:
        try:
            sense = PiProductivity()
        except Exception as e:
            logging.error(
                f"Failed to initialize PiProductivity at startup: {e}", exc_info=True
            )
            sense = None
    if not POSTURE_CSV.exists():
        if sense is not None:
            sense.log_event(POSTURE_CSV, ["timestamp", "ok", "reason", "tilt_deg", "nod_deg", "session_adjustments", "tasks_completed_today"], {"timestamp": datetime.now().isoformat(), "ok": True, "reason": "startup", "tilt_deg": 0, "nod_deg": 0, "session_adjustments": 0, "tasks_completed_today": 0})
    if not TASK_CSV.exists():
        if sense is not None:
            sense.log_task_event("create", "Setup project")

    # If sense init failed, don't start background hardware loop or broadcast.
    if sense is None:
        logging.warning(
            "PiProductivity failed to initialize. Hardware features will be disabled."
        )
        logging.info(f"Log files are located in: {LOG_DIR}")
        logging.info("Starting FastAPI server without hardware integrations...")
        return

    thread = threading.Thread(target=sense.run_forever, daemon=True)
    thread.start()

    asyncio.create_task(broadcast_loop())

    logging.info(f"Database is located at: {sense.db.path}")
    logging.info(f"Log files are located in: {LOG_DIR}")
    logging.info("Starting FastAPI server...")

# --- Main Execution ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
