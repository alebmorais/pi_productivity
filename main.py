import os
import csv
import uuid
import io
import threading
import asyncio
import json
import time
from datetime import datetime
from contextlib import suppress
from pathlib import Path

from fastapi import FastAPI, Request, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
import uvicorn

import sense_mode
from task_database import TaskDatabase
from motion_client import MotionClient
from ocr_notes import OCRNotes, OCRConfig
from epaper import EPD

try:
    import cv2
except ImportError:
    cv2 = None
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

# --- Configuration and Setup ---
BASE_DIR = Path(os.getenv("PI_PRODUCTIVITY_DIR", "~/pi_productivity")).expanduser()
LOG_DIR = BASE_DIR / "logs"
STATIC_DIR = Path(__file__).parent / "static"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

POSTURE_CSV = LOG_DIR / "posture_events.csv"
TASK_CSV = LOG_DIR / "task_events.csv"
LAST_POSTURE_JPEG = BASE_DIR / "last_posture.jpg"

app = FastAPI(title="pi_productivity Web UI")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Database Setup ---
db = TaskDatabase()

# --- Hardware & Service Clients ---
motion_client = MotionClient()
ocr_notes = OCRNotes(OCRConfig())
epaper_display = EPD()

# --- Sense HAT Mode Management ---
sense_modes = {
    "hapvida": sense_mode.HapvidaMode(),
    "careplus": sense_mode.CarePlusMode(),
    "study_adhd": sense_mode.StudyADHDMode(),
    "leisure": sense_mode.LeisureMode(),
}
active_mode = None
active_mode_name = "none"

def stop_current_mode():
    global active_mode, active_mode_name
    if active_mode and active_mode.is_running():
        active_mode.stop()
    active_mode = None
    active_mode_name = "none"

# --- Logging Functions ---
def log_event(file_path, fieldnames, event_data):
    """Appends a new event to a CSV log file."""
    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(event_data)

def log_task_event(action, task_name="", section_title=""):
    """Logs a task creation or completion event."""
    fieldnames = ["timestamp", "action", "task", "section_title"]
    event = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action, # "create" or "complete"
        "task": task_name,
        "section_title": section_title,
    }
    log_event(TASK_CSV, fieldnames, event)
    print(f"Logged task event: action={action}, task={task_name}")

# --- Camera Helpers ---
class Camera:
    def __init__(self):
        self.picam2 = None
        if Picamera2:
            self.picam2 = Picamera2()
            config = self.picam2.create_still_configuration(main={"size": (1280, 720)})
            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(1) # Allow camera to warm up
            print("Camera initialized.")

    def capture_array(self):
        if not self.picam2:
            return None
        return self.picam2.capture_array()

    def read_jpeg(self) -> bytes | None:
        frame = self.capture_array()
        if frame is not None and cv2:
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                # Save the latest capture
                with open(LAST_POSTURE_JPEG, "wb") as f:
                    f.write(buf)
                return bytes(buf)
        
        if LAST_POSTURE_JPEG.exists():
            return LAST_POSTURE_JPEG.read_bytes()
        return None

camera = Camera()
PLACEHOLDER_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \" ,#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13\"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xf7\xfa(\xa2\x80?\xff\xd9"

# --- WebSocket Broadcaster ---
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
        "mode": active_mode_name,
        "sense": get_sense_readings(),
        "tasks": db.fetch_items_for_display(limit=20),
        "timestamp": datetime.utcnow().isoformat(),
    }

# --- Web Application Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "sense_modes": sense_modes.keys(),
        "active_mode": active_mode_name
    })

@app.post("/add_task", response_class=RedirectResponse)
async def add_task(task_name: str = Form(...)):
    log_task_event("create", task_name)
    new_task = {"id": str(uuid.uuid4()), "name": task_name, "status": "pending"}
    db.upsert_motion_tasks([new_task])
    return RedirectResponse("/", status_code=303)

@app.post("/complete_task/{task_id}", response_class=RedirectResponse)
async def complete_task(task_id: str):
    # This is a simplified completion. A more robust implementation 
    # would fetch the task from the DB first to log its name.
    log_task_event("complete", f"task_id:{task_id}")
    completed_task = {"id": task_id, "status": "completed"}
    db.upsert_motion_tasks([completed_task])
    return RedirectResponse("/", status_code=303)

@app.post("/ocr", response_class=JSONResponse)
async def run_ocr():
    frame = await run_in_threadpool(camera.capture_array)
    if frame is None:
        return JSONResponse({"status": "error", "message": "Failed to capture image"}, status_code=500)
    
    img_path, txt_path, text = await run_in_threadpool(ocr_notes.capture_and_ocr, frame)
    
    # Optional: try to create a Motion task from the OCR text
    if motion_client and text:
        try:
            await run_in_threadpool(motion_client.create_task, name=text.split('\n')[0], description=text)
        except Exception as e:
            print(f"Error creating Motion task from OCR: {e}")

    return JSONResponse({"status": "success", "image_path": img_path, "text_path": txt_path, "text": text})

@app.post("/sense/mode", response_class=JSONResponse)
async def set_sense_mode(mode_name: str = Form(...)):
    global active_mode, active_mode_name
    stop_current_mode()
    
    if mode_name in sense_modes:
        active_mode = sense_modes[mode_name]
        active_mode.start()
        active_mode_name = mode_name
        print(f"Started Sense HAT mode: {mode_name}")
    
    return JSONResponse({"status": "success", "mode": active_mode_name})

@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    payload = await run_in_threadpool(build_status_payload)
    return JSONResponse(payload)

@app.get("/camera.jpg")
async def camera_jpeg():
    frame = await run_in_threadpool(camera.read_jpeg)
    data = frame or PLACEHOLDER_JPEG
    return StreamingResponse(io.BytesIO(data), media_type="image/jpeg")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await bus.add(ws)
    try:
        while True:
            await ws.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        bus.remove(ws)

# --- Background Tasks ---
async def broadcast_loop():
    while True:
        payload = await run_in_threadpool(build_status_payload)
        await bus.publish({"kind": "tick", "payload": payload})
        await asyncio.sleep(2)

# --- Background App Logic ---
class App:
    def __init__(self):
        self._last_motion_sync = 0

    def maybe_poll_motion(self):
        if not motion_client or not motion_client.api_key or not db:
            return

        now = time.time()
        interval = 15 * 60  # Sync every 15 minutes
        if now - self._last_motion_sync < interval:
            return

        self._last_motion_sync = now
        try:
            print("[Motion] Starting task sync...")
            tasks = motion_client.list_all_tasks_simple()
            synced = db.upsert_motion_tasks(tasks)
            print(f"[Motion] Synced {synced} tasks.")
            
            # Update e-paper display after syncing
            if epaper_display:
                items = db.fetch_items_for_display()
                epaper_display.render_list(items, title="Pending Tasks")
                print("[E-Paper] Display updated with latest tasks.")

        except Exception as e:
            print(f"[Motion Sync] Error: {e}")

    def run_forever(self):
        print("Starting background hardware loop...")
        while True:
            try:
                self.maybe_poll_motion()
            except Exception as e:
                print(f"Error in background loop: {e}")
            time.sleep(30) # Check every 30 seconds

# --- FastAPI Lifecycle ---
@app.on_event("startup")
async def on_startup():
    # Ensure log files exist for analysis script
    if not POSTURE_CSV.exists():
        log_event(POSTURE_CSV, ["timestamp", "ok"], {"timestamp": datetime.now().isoformat(), "ok": True})
    if not TASK_CSV.exists():
        log_task_event("create", "Setup project")
    
    # Start background tasks
    app_logic = App()
    thread = threading.Thread(target=app_logic.run_forever, daemon=True)
    thread.start()
    
    asyncio.create_task(broadcast_loop())
    
    print(f"Database is located at: {db.path}")
    print(f"Log files are located in: {LOG_DIR}")
    print("Starting FastAPI server...")

# --- Main Execution ---
if __name__ == "__main__":
    # Make sure to set the PI_PRODUCTIVITY_DIR environment variable
    # example: export PI_PRODUCTIVITY_DIR=/path/to/your/project
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

    # ---------------- Postura / OCR (uma execução) ----------------
    def _ensure_camera(self):
        # lazy init
        if not hasattr(self, "cam"):
            with self._cam_lock:
                if not hasattr(self, "cam"):
                    from picamera2 import Picamera2
                    self.cam = Picamera2()
                    self.cam.configure(self.cam.create_still_configuration())
                    self.cam.start()
            
    def run_posture_once(self):
        from sense_mode import RED, GREEN
        self._ensure_camera()
        status = {}
        try:
            with self._cam_lock:
                frame = self.cam.capture_array()
                if frame is None:
                    raise ValueError("Falha ao capturar frame da câmera.")
                
                status = self.posture.analyze_frame(frame)
                self._log_posture_csv(status)
                
                try:
                    import cv2
                    cv2.imwrite(os.path.join(BASE_DIR, "last_posture.jpg"), frame)
                except Exception as e:
                    print(f"[Posture] erro ao salvar imagem: {e}")

        except Exception as e:
            print(f"[PostureLog] aviso: {e}")
            status = {'ok': False, 'reason': 'exception'}

        self._flash(GREEN if status.get("ok") else RED, times=3)
        self._show_mode_pattern(self.MODES[self.mode_index])
        return status

    def run_ocr_once(self):
        self._ensure_camera()
        with self._cam_lock:
            frame = self.cam.capture_array()
            img_path, txt_path, text = self.ocr.capture_and_ocr(frame)
        try:
            if MOTION_ENABLE_OCR and hasattr(self, "_ocr_apply_to_motion"):
                self._ocr_apply_to_motion(text)
        except Exception as e:
            print("[OCR→Motion] erro:", e)
        self._flash([0,255,255], times=3)  # ciano
        print(f"OCR salvo em: {txt_path}")
        self._show_mode_pattern(self.MODES[self.mode_index])
        return img_path, txt_path, text

    # ---------------- OCR → Ações (parser por seção/título) ----------------
    def _ocr_parse_actions(self, text):
        """
        Formato:
        Título da Seção
        - [ ] Fazer X
        - [x] Concluir Y
        DUE: 2025-10-05

        ou:
        Título
        TODO: Algo
        DONE: Algo
        """
        actions = []
        lines = [l.rstrip() for l in text.splitlines()]
        current_section = None; pending_due = None

        def add_create(name):
            actions.append({"type":"create","name":name.strip(),"due":pending_due,"section":current_section})
        def add_complete(name):
            actions.append({"type":"complete","name":name.strip(),"section":current_section})

        i=0
        while i < len(lines):
            line = lines[i].strip()
            low  = line.lower()
            if not line:
                i+=1; continue
            if low.startswith("due:"):
                pending_due = line.split(":",1)[1].strip(); i+=1; continue
            if low.startswith("- [ ]"):
                add_create(line.split("]",1)[-1].strip()); i+=1; continue
            if low.startswith("- [x]"):
                add_complete(line.split("]",1)[-1].strip()); i+=1; continue
            if low.startswith("todo:"):
                add_create(line.split(":",1)[1].strip()); i+=1; continue
            if low.startswith("done:"):
                add_complete(line.split(":",1)[1].strip()); i+=1; continue
            # Título de seção
            current_section = line.strip()
            pending_due = None
            i+=1
        return actions

    def _iso_from_due_hint(self, due_hint):
        from datetime import datetime, timedelta, timezone
        days = OCR_DEFAULT_DUE_DAYS
        if due_hint:
            try:
                d = datetime.fromisoformat(due_hint.strip())
                d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                return d.isoformat().replace("+00:00","Z")
            except Exception:
                pass
        d = datetime.utcnow() + timedelta(days=days)
        d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        return d.isoformat().replace("+00:00","Z")

    def _ocr_apply_to_motion(self, text):
        if not self.motion:
            print("[OCR→Motion] MotionClient indisponível.")
            return
        acts = self._ocr_parse_actions(text)
        if not acts:
            print("[OCR→Motion] nenhum comando reconhecido no texto")
            return
        created=0; completed=0
        for a in acts:
            section = a.get("section") or ""
            try:
                if a["type"]=="create":
                    due_iso = self._iso_from_due_hint(a.get("due"))
                    self.motion.create_task(name=a["name"], description="(via OCR)", due_date_iso=due_iso, labels=[section] if section else None)
                    created += 1
                    self._log_task_event("create", section, a["name"])
                elif a["type"]=="complete":
                    t = self.motion.find_task_by_name(a["name"])
                    if t:
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
                    else:
                        t = self.motion.create_task(name=a["name"], description="(via OCR, auto-complete)", labels=[section] if section else None)
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
            except Exception as e:
                print("[OCR→Motion] erro:", e)
        print(f"[OCR→Motion] criadas={created} concluídas={completed}")

    # ---------------- Loops automáticos ----------------
    def _auto_posture_loop(self):
        while True:
            try:
                st = self.run_posture_once()
                ok = "OK" if st.get("ok") else f"AJUSTAR ({st.get('reason')})"
                print(f"[Auto/Postura] {ok} | tilt={st.get('tilt'):.1f}° nod={st.get('nod'):.1f}°")
            except Exception as e:
                print("[Auto/Postura] Erro:", e)
            time.sleep(max(5, POSTURE_INTERVAL))

    def _auto_ocr_loop(self):
        while True:
            try:
                img, txt, _ = self.run_ocr_once()
                print(f"[Auto/OCR] Salvo: {img} | {txt}")
            except Exception as e:
                print("[Auto/OCR] Erro:", e)
            time.sleep(max(5, OCR_INTERVAL))

    # ---------------- UI básica ----------------
    def _render_mode_banner(self):
        name = self.MODES[self.mode_index]
        print(f"[Sense] Modo: {name}")
        self._show_mode_pattern(name)
        self._update_epaper_display(name)

    def _update_epaper_display(self, mode_name):
        if not self.epaper:
            return

        try:
            if "TRABALHO" in mode_name or "ESTUDO" in mode_name:
                if self.motion:
                    tasks = self.motion.list_all_tasks_simple()
                    items = []
                    for task in tasks[:5]: # Limita a 5 para caber na tela
                        items.append({"title": task.get("name", "...")})
                    self.epaper.render_list(items, title=mode_name)
                else:
                    self.epaper.render_tip("Motion client não disponível.", title=mode_name)
            elif mode_name == "POSTURA":
                self.epaper.render_tip("Mantenha a cabeça erguida e os ombros relaxados.", title="Dica de Postura")
            elif mode_name == "OCR NOTAS":
                self.epaper.render_tip("Centralize o texto e aperte o joystick para capturar.", title="OCR")
            else:
                self.epaper.render_tip(f"Modo {mode_name} ativado.", title="Info")
        except Exception as e:
            print(f"[E-Paper] Erro ao atualizar: {e}")

    def handle_joystick(self, event):
        if event.action not in ("pressed", "held"):
            return
        delta = 0
        if event.direction in ("right", "up"):
            delta = 1
        elif event.direction in ("left", "down"):
            delta = -1
        else:
            return

        prev_mode = self.MODES[self.mode_index]
        self.mode_index = (self.mode_index + delta) % len(self.MODES)
        self._render_mode_banner()
        self._apply_mode_logic(prev_mode, self.MODES[self.mode_index])

    def _apply_mode_logic(self, previous_mode, current_mode):
        previous_timer = self._mode_timers.get(previous_mode)
        new_timer = self._mode_timers.get(current_mode)

        if previous_timer and previous_timer is not new_timer:
            previous_timer.stop()
            if self._active_timer is previous_timer:
                self._active_timer = None
            if new_timer is None:
                self._render_mode_banner()

        if new_timer:
            if self._active_timer is not new_timer:
                new_timer.start()
                self._active_timer = new_timer
        else:
            self._active_timer = None

    def maybe_poll_motion(self):
        if not self.task_db:
            return

        now = time.time()
        interval = max(60, MOTION_SYNC_INTERVAL)
        if now - self._last_motion_sync < interval:
            return

        self._last_motion_sync = now
        synced = 0
        if self.motion:
            try:
                tasks = self.motion.list_all_tasks_simple()
                synced = self.task_db.upsert_motion_tasks(tasks)
                print(f"[Motion] sincronizou {synced} tarefas")
            except Exception as e:
                print("[Motion] erro ao sincronizar tarefas:", e)

        if self.epaper:
            try:
                items = self.task_db.fetch_items_for_display()
                path = self.epaper.render_list(items)
                print(f"[EPaper] Atualizado: {path}")
            except Exception as e:
                print("[EPaper] erro ao atualizar display:", e)

    def run(self):
        self._render_mode_banner()
        sense.stick.direction_any = self.handle_joystick
        while True:
            self.maybe_poll_motion()
            time.sleep(1)

class PiProductivity:
    # ---------------- Postura / OCR (uma execução) ----------------
    def _ensure_camera(self):
        # lazy init
        if not hasattr(self, "cam"):
            with self._cam_lock:
                if not hasattr(self, "cam"):
                    from picamera2 import Picamera2
                    self.cam = Picamera2()
                    self.cam.configure(self.cam.create_still_configuration())
                    self.cam.start()
            
    def run_posture_once(self):
        from sense_mode import RED, GREEN
        self._ensure_camera()
        status = {}
        try:
            with self._cam_lock:
                frame = self.cam.capture_array()
                if frame is None:
                    raise ValueError("Falha ao capturar frame da câmera.")
                
                status = self.posture.analyze_frame(frame)
                self._log_posture_csv(status)
                
                try:
                    import cv2
                    cv2.imwrite(os.path.join(BASE_DIR, "last_posture.jpg"), frame)
                except Exception as e:
                    print(f"[Posture] erro ao salvar imagem: {e}")

        except Exception as e:
            print(f"[PostureLog] aviso: {e}")
            status = {'ok': False, 'reason': 'exception'}

        self._flash(GREEN if status.get("ok") else RED, times=3)
        self._show_mode_pattern(self.MODES[self.mode_index])
        return status

    def run_ocr_once(self):
        self._ensure_camera()
        with self._cam_lock:
            frame = self.cam.capture_array()
            img_path, txt_path, text = self.ocr.capture_and_ocr(frame)
        try:
            if MOTION_ENABLE_OCR and hasattr(self, "_ocr_apply_to_motion"):
                self._ocr_apply_to_motion(text)
        except Exception as e:
            print("[OCR→Motion] erro:", e)
        self._flash([0,255,255], times=3)  # ciano
        print(f"OCR salvo em: {txt_path}")
        self._show_mode_pattern(self.MODES[self.mode_index])
        return img_path, txt_path, text

    # ---------------- OCR → Ações (parser por seção/título) ----------------
    def _ocr_parse_actions(self, text):
        """
        Formato:
        Título da Seção
        - [ ] Fazer X
        - [x] Concluir Y
        DUE: 2025-10-05

        ou:
        Título
        TODO: Algo
        DONE: Algo
        """
        actions = []
        lines = [l.rstrip() for l in text.splitlines()]
        current_section = None; pending_due = None

        def add_create(name):
            actions.append({"type":"create","name":name.strip(),"due":pending_due,"section":current_section})
        def add_complete(name):
            actions.append({"type":"complete","name":name.strip(),"section":current_section})

        i=0
        while i < len(lines):
            line = lines[i].strip()
            low  = line.lower()
            if not line:
                i+=1; continue
            if low.startswith("due:"):
                pending_due = line.split(":",1)[1].strip(); i+=1; continue
            if low.startswith("- [ ]"):
                add_create(line.split("]",1)[-1].strip()); i+=1; continue
            if low.startswith("- [x]"):
                add_complete(line.split("]",1)[-1].strip()); i+=1; continue
            if low.startswith("todo:"):
                add_create(line.split(":",1)[1].strip()); i+=1; continue
            if low.startswith("done:"):
                add_complete(line.split(":",1)[1].strip()); i+=1; continue
            # Título de seção
            current_section = line.strip()
            pending_due = None
            i+=1
        return actions

    def _iso_from_due_hint(self, due_hint):
        from datetime import datetime, timedelta, timezone
        days = OCR_DEFAULT_DUE_DAYS
        if due_hint:
            try:
                d = datetime.fromisoformat(due_hint.strip())
                d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                return d.isoformat().replace("+00:00","Z")
            except Exception:
                pass
        d = datetime.utcnow() + timedelta(days=days)
        d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        return d.isoformat().replace("+00:00","Z")

    def _ocr_apply_to_motion(self, text):
        if not self.motion:
            print("[OCR→Motion] MotionClient indisponível.")
            return
        acts = self._ocr_parse_actions(text)
        if not acts:
            print("[OCR→Motion] nenhum comando reconhecido no texto")
            return
        created=0; completed=0
        for a in acts:
            section = a.get("section") or ""
            try:
                if a["type"]=="create":
                    due_iso = self._iso_from_due_hint(a.get("due"))
                    self.motion.create_task(name=a["name"], description="(via OCR)", due_date_iso=due_iso, labels=[section] if section else None)
                    created += 1
                    self._log_task_event("create", section, a["name"])
                elif a["type"]=="complete":
                    t = self.motion.find_task_by_name(a["name"])
                    if t:
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
                    else:
                        t = self.motion.create_task(name=a["name"], description="(via OCR, auto-complete)", labels=[section] if section else None)
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
            except Exception as e:
                print("[OCR→Motion] erro:", e)
        print(f"[OCR→Motion] criadas={created} concluídas={completed}")

    # ---------------- Loops automáticos ----------------
    def _auto_posture_loop(self):
        while True:
            try:
                st = self.run_posture_once()
                ok = "OK" if st.get("ok") else f"AJUSTAR ({st.get('reason')})"
                print(f"[Auto/Postura] {ok} | tilt={st.get('tilt'):.1f}° nod={st.get('nod'):.1f}°")
            except Exception as e:
                print("[Auto/Postura] Erro:", e)
            time.sleep(max(5, POSTURE_INTERVAL))

    def _auto_ocr_loop(self):
        while True:
            try:
                img, txt, _ = self.run_ocr_once()
                print(f"[Auto/OCR] Salvo: {img} | {txt}")
            except Exception as e:
                print("[Auto/OCR] Erro:", e)
            time.sleep(max(5, OCR_INTERVAL))

    # ---------------- UI básica ----------------
    def _render_mode_banner(self):
        name = self.MODES[self.mode_index]
        print(f"[Sense] Modo: {name}")
        self._show_mode_pattern(name)
        self._update_epaper_display(name)

    def _update_epaper_display(self, mode_name):
        if not self.epaper:
            return

        try:
            if "TRABALHO" in mode_name or "ESTUDO" in mode_name:
                if self.motion:
                    tasks = self.motion.list_all_tasks_simple()
                    items = []
                    for task in tasks[:5]: # Limita a 5 para caber na tela
                        items.append({"title": task.get("name", "...")})
                    self.epaper.render_list(items, title=mode_name)
                else:
                    self.epaper.render_tip("Motion client não disponível.", title=mode_name)
            elif mode_name == "POSTURA":
                self.epaper.render_tip("Mantenha a cabeça erguida e os ombros relaxados.", title="Dica de Postura")
            elif mode_name == "OCR NOTAS":
                self.epaper.render_tip("Centralize o texto e aperte o joystick para capturar.", title="OCR")
            else:
                self.epaper.render_tip(f"Modo {mode_name} ativado.", title="Info")
        except Exception as e:
            print(f"[E-Paper] Erro ao atualizar: {e}")

    def handle_joystick(self, event):
        if event.action not in ("pressed", "held"):
            return
        delta = 0
        if event.direction in ("right", "up"):
            delta = 1
        elif event.direction in ("left", "down"):
            delta = -1
        else:
            return

        prev_mode = self.MODES[self.mode_index]
        self.mode_index = (self.mode_index + delta) % len(self.MODES)
        self._render_mode_banner()
        self._apply_mode_logic(prev_mode, self.MODES[self.mode_index])

    def _apply_mode_logic(self, previous_mode, current_mode):
        previous_timer = self._mode_timers.get(previous_mode)
        new_timer = self._mode_timers.get(current_mode)

        if previous_timer and previous_timer is not new_timer:
            previous_timer.stop()
            if self._active_timer is previous_timer:
                self._active_timer = None
            if new_timer is None:
                self._render_mode_banner()

        if new_timer:
            if self._active_timer is not new_timer:
                new_timer.start()
                self._active_timer = new_timer
        else:
            self._active_timer = None

    def maybe_poll_motion(self):
        if not self.task_db:
            return

        now = time.time()
        interval = max(60, MOTION_SYNC_INTERVAL)
        if now - self._last_motion_sync < interval:
            return

        self._last_motion_sync = now
        synced = 0
        if self.motion:
            try:
                tasks = self.motion.list_all_tasks_simple()
                synced = self.task_db.upsert_motion_tasks(tasks)
                print(f"[Motion] sincronizou {synced} tarefas")
            except Exception as e:
                print("[Motion] erro ao sincronizar tarefas:", e)

        if self.epaper:
            try:
                items = self.task_db.fetch_items_for_display()
                path = self.epaper.render_list(items)
                print(f"[EPaper] Atualizado: {path}")
            except Exception as e:
                print("[EPaper] erro ao atualizar display:", e)

    def run(self):
        self._render_mode_banner()
        sense.stick.direction_any = self.handle_joystick
        while True:
            self.maybe_poll_motion()
            time.sleep(1)

if __name__ == "__main__":
    # Create a single, global instance of your main application class
    sense = PiProductivity()

    # Now, your FastAPI endpoints and other functions can use the 'sense' object
    @app.get("/status")
    def get_status():
        # This function can now safely use the 'sense' object
        return {"mode": sense.MODES[sense.mode_index]}

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

MOTION_ENABLE_OCR = True
OCR_DEFAULT_DUE_DAYS = 7
POSTURE_INTERVAL = 300 # 5 minutes in seconds
OCR_INTERVAL = 900     # 15 minutes in seconds
MOTION_SYNC_INTERVAL = 600 # 10 minutes in seconds
