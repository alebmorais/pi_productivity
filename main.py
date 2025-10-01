import os, time, threading
from dotenv import load_dotenv
from motion_client import MotionClient
from epaper_display import EPaperDisplay
from sense_modes import HapvidaMode, CarePlusMode, StudyADHDMode, LeisureMode, sense
from motion_client import MotionClient
from epaper_display import EPaperDisplay
from sense_modes import HapvidaMode, CarePlusMode, StudyADHDMode, LeisureMode, sense
from utils import today_local
from datetime import datetime
from picamera2 import Picamera2
import cv2
from camera_posture import PostureMonitor, PostureConfig
from ocr_notes import OCRNotes, OCRConfig
import os, time, threading, csv
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/pi_productivity/.env"))

# ===== Configs de loops automáticos =====
AUTO_POSTURE = os.getenv("AUTO_POSTURE","1") == "1"
POSTURE_INTERVAL = int(os.getenv("POSTURE_INTERVAL_SEC","30"))

AUTO_OCR = os.getenv("AUTO_OCR","1") == "1"
OCR_INTERVAL = int(os.getenv("OCR_INTERVAL_SEC","900"))

# ===== Hidratação =====
HYDRATE_ENABLE = os.getenv("HYDRATE_ENABLE","1") == "1"
HYDRATE_INTERVAL_MIN = int(os.getenv("HYDRATE_INTERVAL_MIN","40"))
HYDRATE_FLASHES = int(os.getenv("HYDRATE_FLASHES","6"))
HYDRATE_ON_SEC = float(os.getenv("HYDRATE_ON_SEC","0.25"))
HYDRATE_OFF_SEC = float(os.getenv("HYDRATE_OFF_SEC","0.15"))

# ===== OCR → Motion =====
MOTION_ENABLE_OCR = os.getenv("MOTION_ENABLE_OCR","0") == "1"
OCR_DEFAULT_DUE_DAYS = int(os.getenv("OCR_DEFAULT_DUE_DAYS","2"))

# ===== Logs (CSV/TXT) =====
LOG_DIR = os.path.expanduser("~/pi_productivity/logs")
os.makedirs(LOG_DIR, exist_ok=True)
POSTURE_CSV = os.path.join(LOG_DIR, "posture_events.csv")
TASK_CSV    = os.path.join(LOG_DIR, "task_events.csv")

def _ensure_csv_headers():
    if not os.path.exists(POSTURE_CSV):
        with open(POSTURE_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["timestamp","ok","reason","tilt_deg","nod_deg","session_adjustments","tasks_completed_today"]
            )
    if not os.path.exists(TASK_CSV):
        with open(TASK_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["timestamp","action","section_title","task_name"]
            )
_ensure_csv_headers()


load_dotenv()

HYDRATE_ENABLE = os.getenv("HYDRATE_ENABLE","1") == "1"
HYDRATE_INTERVAL_MIN = int(os.getenv("HYDRATE_INTERVAL_MIN","40"))
HYDRATE_FLASHES = int(os.getenv("HYDRATE_FLASHES","6"))
HYDRATE_ON_SEC = float(os.getenv("HYDRATE_ON_SEC","0.25"))
HYDRATE_OFF_SEC = float(os.getenv("HYDRATE_OFF_SEC","0.15"))

AUTO_POSTURE = os.getenv("AUTO_POSTURE", "0") == "1"
POSTURE_INTERVAL = int(os.getenv("POSTURE_INTERVAL_SEC", "30"))

AUTO_OCR = os.getenv("AUTO_OCR", "0") == "1"
OCR_INTERVAL = int(os.getenv("OCR_INTERVAL_SEC", "900"))

POLL_MINUTES = int(os.getenv("MOTION_POLL_MINUTES","12"))

class App:
    MODES = ["TAREFAS","TRABALHO: HAPVIDA","TRABALHO: CARE PLUS","ESTUDO (TDAH)","LAZER","POSTURA","OCR NOTAS"]
    def __init__(self):
        self.motion = MotionClient()
        self.display = EPaperDisplay()
        self.mode_index = 0
        self.last_tasks = []
        self.running_mode = None
        self.hapvida = HapvidaMode()
        self.careplus = CarePlusMode()
        self.study = StudyADHDMode()
        self.leisure = LeisureMode()
        # Camera / AI
        self.cam = None
        self.posture = PostureMonitor(PostureConfig())
        self.ocr = OCRNotes(OCRConfig())
        self._lock = threading.Lock()
        self._last_poll = 0
        self._auto_threads = []
        if AUTO_POSTURE:
            t = threading.Thread(target=self._auto_posture_loop, daemon=True)
            t.start()
            self._auto_threads.append(t)
            print(f"[Auto] Postura ligado (cada {POSTURE_INTERVAL}s)")
        if AUTO_OCR:
            t = threading.Thread(target=self._auto_ocr_loop, daemon=True)
            t.start()
            self._auto_threads.append(t)
            print(f"[Auto] OCR ligado (cada {OCR_INTERVAL}s)")
        if HYDRATE_ENABLE:
            t = threading.Thread(target=self._hydrate_loop, daemon=True)
            t.start()
            self._auto_threads.append(t)
            print(f"[Auto] Hidratação ligada (cada {HYDRATE_INTERVAL_MIN} min)")

        # Estado da sessão
        self.posture_adjust_count = 0
        self.tasks_completed_today = 0
        self._tasks_completed_date = time.strftime("%Y-%m-%d")
        self.posture_log_path = os.path.join(LOG_DIR, time.strftime("posture_%Y%m%d.txt"))

        # Threads automáticas
        self._auto_threads = []
        if AUTO_POSTURE:
            t = threading.Thread(target=self._auto_posture_loop, daemon=True)
            t.start(); self._auto_threads.append(t)
            print(f"[Auto] Postura ligada (cada {POSTURE_INTERVAL}s)")
        if AUTO_OCR:
            t = threading.Thread(target=self._auto_ocr_loop, daemon=True)
            t.start(); self._auto_threads.append(t)
            print(f"[Auto] OCR ligado (cada {OCR_INTERVAL}s)")
        if HYDRATE_ENABLE:
            t = threading.Thread(target=self._hydrate_loop, daemon=True)
            t.start(); self._auto_threads.append(t)
            print(f"[Auto] Hidratação ligada (cada {HYDRATE_INTERVAL_MIN} min)")

def _ensure_camera(self):
        if self.cam is None:
            self.cam = Picamera2()
            self.cam.configure(self.cam.create_preview_configuration(main={"size": (640,480)}))
            self.cam.start()

    def run_posture_once(self):
        from sense_modes import RED, GREEN
        self._ensure_camera()
        frame = self.cam.capture_array()
        status = self.posture.analyze_frame(frame)

        # (seu contador/log permanecem — se tiver, mantenha chamadas aqui)
        if status.get("ok"):
            self._flash(GREEN, times=3)
        else:
            self._flash(RED, times=3)

        try:
            import cv2
            cv2.imwrite("/home/pi/pi_productivity/last_posture.jpg", frame)
        except Exception:
            pass

        self._show_mode_pattern(self.MODES[self.mode_index])
        return status

    def run_ocr_once(self):
        self._ensure_camera()
        frame = self.cam.capture_array()
        img_path, txt_path, text = self.ocr.capture_and_ocr(frame)

        # (seu fluxo OCR→Motion permanece — se tiver, chame aqui)
        try:
            self._ocr_apply_to_motion(text)  # se você já implementou, mantenha
        except Exception as e:
            print("[OCR→Motion] erro:", e)

        self._flash([0,255,255], times=3)  # ciano
        print(f"OCR salvo em: {txt_path}")
        self._show_mode_pattern(self.MODES[self.mode_index])
        return img_path, txt_path, text

    def show_tip_study(self):
        tips = [
            "Defina 1 meta clara para os 20 min.",
            "Use papel e caneta; tire distrações do alcance.",
            "Regra dos 3: meta de hoje, próxima tarefa, tempo.",
            "Pausa de 10 min: água, alongar, 4-7-8 respiração.",
            "Recompense-se após 3 ciclos concluídos.",
        ]
        self.display.render_tip(tips[int(time.time()) % len(tips)])

    def stop_current_mode(self):
        if self.running_mode:
            self.running_mode.stop()
            self.running_mode = None
            self._flash([255,255,255], times=1)  # branco ao parar
        self._show_mode_pattern(self.MODES[self.mode_index])  # restaura padrão
"Regra dos 3: meta de hoje, próxima tarefa, tempo.",
            "Pausa de 10 min: água, alongar, 4-7-8 respiração.",
            "Recompense-se após 3 ciclos concluídos.",
        ]
        self.display.render_tip(tips[int(time.time()) % len(tips)])

    def stop_current_mode(self):
        if self.running_mode:
            self.running_mode.stop()
            self.running_mode = None
            self._flash([255,255,255], times=1)  # branco ao parar
        self._show_mode_pattern(self.MODES[self.mode_index])  # restaura padrão


    def start_mode(self, name):
        self.stop_current_mode()
        if name == "TRABALHO: HAPVIDA":
            self.running_mode = self.hapvida
        elif name == "TRABALHO: CARE PLUS":
            self.running_mode = self.careplus
        elif name == "ESTUDO (TDAH)":
            self.running_mode = self.study
        elif name == "LAZER":
            self.running_mode = self.leisure
        else:
            self.running_mode = None
        if self.running_mode:
            self.running_mode.start()
            self._flash([0,255,0], times=2)  # verde ao iniciar

    def handle_joystick(self, event):
        if event.action != "pressed":
            return
        if event.direction == "up":
            self.mode_index = (self.mode_index - 1) % len(self.MODES)
            self.stop_current_mode()
            self._render_mode_banner()
        elif event.direction == "down":
            self.mode_index = (self.mode_index + 1) % len(self.MODES)
            self.stop_current_mode()
            self._render_mode_banner()
        elif event.direction == "right":
            current = self.MODES[self.mode_index]
            if current in ["POSTURA", "OCR NOTAS"]:
            if current == "POSTURA":
                status = self.run_posture_once()
                print("Postura:", status)
              else:
                self.run_ocr_once()
              else:
                self.start_mode(current)
             if current == "ESTUDO (TDAH)":
                self.show_tip_study()
        elif event.direction == "left":
            self.stop_current_mode()
        elif event.direction == "middle":
            self.show_tasks(force=True)

    def _show_mode_pattern(self, name):
        from sense_modes import sense
        BLACK = [0,0,0]
        W = [255,255,255]; G = [0,255,0]; B = [0,0,255]
def set_pixels(rows):
            flat = []
            for row in rows:
                flat.extend(row)
            sense.set_pixels(flat)

        # Padrões por modo
        if name == "TAREFAS":
            # tabuleiro (branco/preto)
            rows = [[W if (x+y)%2==0 else BLACK for x in range(8)] for y in range(8)]
        elif name == "TRABALHO: HAPVIDA":
            # barras verdes (metade da esquerda)
            rows = [[G if x < 4 else BLACK for x in range(8)] for _ in range(8)]
        elif name == "TRABALHO: CARE PLUS":
            # diagonais azuis
            rows = [[B if (x==y or x+y==7) else BLACK for x in range(8)] for y in range(8)]
        elif name == "ESTUDO (TDAH)":
            # “aro” amarelo
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(Y if (x in (1,6) or y in (1,6)) else BLACK)
                    rows.append(row)
        elif name == "LAZER":
            # bloco magenta
            rows = [[M for _ in range(8)] for _ in range(8)]
        elif name == "POSTURA":
            # cruz vermelha
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(R if (x==3 or y==3) else BLACK)
                rows.append(row)
        elif name == "OCR NOTAS":
            # “livro” ciano
            rows = [[BLACK]*8 for _ in range(8)]
            for y in range(2,6):
                rows[y][2] = C; rows[y][5] = C
            for x in range(2,6):
                rows[2][x] = C; rows[5][x] = C
            rows[3][3] = C; rows[4][4] = C
        else:
            rows = [[W]*8 for _ in range(8)]

        set_pixels(rows)

    def _render_mode_banner(self):
        name = self.MODES[self.mode_index]
        print(f"[Sense] Modo: {name}")
        self._show_mode_pattern(name)
        if name == "TAREFAS":
            self.show_tasks(force=False)
        elif name == "ESTUDO (TDAH)":
            self.show_tip_study()                                                                                     
        elif name == "ESTUDO (TDAH)":
            self.show_tip_study()

    def maybe_poll_motion(self):
        now = time.time()
        if (now - self._last_poll) >= POLL_MINUTES*60:
            self.show_tasks(force=True)
            self._last_poll = now
    def _flash(self, color, times=2, on=0.15, off=0.10):
        from sense_modes import sense
        import time as _t
        for _ in range(times):
            sense.clear(color); _t.sleep(on)
            sense.clear(); _t.sleep(off)

    def _show_mode_pattern(self, name):
        from sense_modes import sense
        BLACK = [0,0,0]
        W = [255,255,255]; G = [0,255,0]; B = [0,0,255]
        Y = [255,255,0];   M = [128,0,255]; R = [255,0,0]; C = [0,255,255]

        def set_pixels(rows):
            flat = []
            for row in rows: flat.extend(row)
            sense.set_pixels(flat)

        if name == "TAREFAS":
            rows = [[W if (x+y)%2==0 else BLACK for x in range(8)] for y in range(8)]
        elif name == "TRABALHO: HAPVIDA":
            rows = [[G if x < 4 else BLACK for x in range(8)] for _ in range(8)]
        elif name == "TRABALHO: CARE PLUS":
            rows = [[B if (x==y or x+y==7) else BLACK for x in range(8)] for y in range(8)]
        elif name == "ESTUDO (TDAH)":
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(Y if (x in (1,6) or y in (1,6)) else BLACK)
                rows.append(row)
        elif name == "LAZER":
            rows = [[M for _ in range(8)] for _ in range(8)]
        elif name == "POSTURA":
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(R if (x==3 or y==3) else BLACK)
                rows.append(row)
        elif name == "OCR NOTAS":
            rows = [[BLACK]*8 for _ in range(8)]
            for y in range(2,6):
                rows[y][2] = C; rows[y][5] = C
            for x in range(2,6):
                rows[2][x] = C; rows[5][x] = C
            rows[3][3] = C; rows[4][4] = C
        else:
            rows = [[W]*8 for _ in range(8)]
        set_pixels(rows)
row = []
                for x in range(8):
                    row.append(R if (x==3 or y==3) else BLACK)
                rows.append(row)
        elif name == "OCR NOTAS":
            rows = [[BLACK]*8 for _ in range(8)]
            for y in range(2,6):
                rows[y][2] = C; rows[y][5] = C
            for x in range(2,6):
                rows[2][x] = C; rows[5][x] = C
            rows[3][3] = C; rows[4][4] = C
        else:
            rows = [[W]*8 for _ in range(8)]
        set_pixels(rows)

    # ——— Hidratação (gota azul-clara) ———
    def _show_hydration_drop(self):
        from sense_modes import sense
        BLACK = [0,0,0]
        DROP  = [0,180,255]
        rows = [[BLACK]*8 for _ in range(8)]
        coords = [(1,3,4),(2,2,5),(3,2,5),(4,3,4),(5,3,4),(6,3,4)]
        for y,x0,x1 in coords:
            for x in range(x0, x1+1):
                rows[y][x] = DROP
        flat = []
        for row in rows: flat.extend(row)
        sense.set_pixels(flat)

    def _hydrate_blink(self):
        from sense_modes import sense
        import time as _t
        for _ in range(max(1, HYDRATE_FLASHES)):
            self._show_hydration_drop()
            _t.sleep(HYDRATE_ON_SEC)
            sense.clear()
            _t.sleep(HYDRATE_OFF_SEC)
        self._show_mode_pattern(self.MODES[self.mode_index])

    def _hydrate_loop(self):
        import time as _t
        next_ts = _t.time() + HYDRATE_INTERVAL_MIN*60
        while True:
            _t.sleep(1)
            if _t.time() >= next_ts:
                try:
                    print("[Hydrate] lembrete de hidratação")
                    self._hydrate_blink()
                except Exception as e:
                    print("[Hydrate] erro:", e)
                next_ts = _t.time() + HYDRATE_INTERVAL_MIN*60
    def _flash(self, color, times=2, on=0.15, off=0.10):
        from sense_modes import sense
        for _ in range(times):
            sense.clear(color); time.sleep(on)
            sense.clear();      time.sleep(off)

    def _show_mode_pattern(self, name):
        from sense_modes import sense
        BLACK = [0,0,0]
        W = [255,255,255]; G = [0,255,0]; B = [0,0,255]
        Y = [255,255,0];   M = [128,0,255]; R = [255,0,0]; C = [0,255,255]

        def set_pixels(rows):
            flat=[]; [flat.extend(r) for r in rows]
            sense.set_pixels(flat)

        # mapeamento simples pelos nomes que você usa na UI
        if name == "TAREFAS":
            rows = [[W if (x+y)%2==0 else BLACK for x in range(8)] for y in range(8)]
        elif name == "TRABALHO: HAPVIDA":
            rows = [[G if x < 4 else BLACK for x in range(8)] for _ in range(8)]
        elif name == "TRABALHO: CARE PLUS":
            rows = [[B if (x==y or x+y==7) else BLACK for x in range(8)] for y in range(8)]
        elif name == "ESTUDO (TDAH)":
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(Y if (x in (1,6) or y in (1,6)) else BLACK)
                rows.append(row)
        elif name == "LAZER":
            rows = [[M for _ in range(8)] for _ in range(8)]
        elif name == "POSTURA":
            rows = []
            for y in range(8):
                row = []
                for x in range(8):
                    row.append(R if (x==3 or y==3) else BLACK)
                rows.append(row)
        elif name == "OCR NOTAS":
            rows = [[BLACK]*8 for _ in range(8)]
            for y in range(2,6):
                rows[y][2] = C; rows[y][5] = C
            for x in range(2,6):
                rows[2][x] = C; rows[5][x] = C
            rows[3][3] = C; rows[4][4] = C
        else:
            rows = [[W]*8 for _ in range(8)]
        set_pixels(rows)

    def _render_mode_banner(self):
        name = self.MODES[self.mode_index]
        print(f"[Sense] Modo: {name}")
        self._show_mode_pattern(name)
        if name == "TAREFAS":
            self.show_tasks(force=False)
        elif name == "ESTUDO (TDAH)":
            self.show_tip_study()
    def _show_hydration_drop(self):
        from sense_modes import sense
        BLACK = [0,0,0]
        DROP  = [0,180,255]
        rows = [[BLACK]*8 for _ in range(8)]
        coords = [(1,3,4),(2,2,5),(3,2,5),(4,3,4),(5,3,4),(6,3,4)]
        for y,x0,x1 in coords:
            for x in range(x0, x1+1):
                rows[y][x] = DROP
        flat=[]; [flat.extend(r) for r in rows]
        sense.set_pixels(flat)

    def _hydrate_blink(self):
        from sense_modes import sense
        for _ in range(max(1, HYDRATE_FLASHES)):
            self._show_hydration_drop()
            time.sleep(HYDRATE_ON_SEC)
            sense.clear()
            time.sleep(HYDRATE_OFF_SEC)
        self._show_mode_pattern(self.MODES[self.mode_index])

    def _hydrate_loop(self):
        next_ts = time.time() + HYDRATE_INTERVAL_MIN*60
        while True:
            time.sleep(1)
            if time.time() >= next_ts:
                try:
                    print("[Hydrate] lembrete de hidratação")
                    self._hydrate_blink()
                except Exception as e:
                    print("[Hydrate] erro:", e)
                next_ts = time.time() + HYDRATE_INTERVAL_MIN*60
    def _maybe_reset_completed_counter(self):
        today = time.strftime("%Y-%m-%d")
        if getattr(self, "_tasks_completed_date", None) != today:
            self._tasks_completed_date = today
            self.tasks_completed_today = 0

    def _log_task_event(self, action, section_title, task_name):
        self._maybe_reset_completed_counter()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(TASK_CSV, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([ts, action, section_title or "", task_name or ""])
        except Exception as e:
            print("[TaskLog] erro:", e)
        if action == "complete":
            self.tasks_completed_today += 1

    def _log_posture_text(self, status):
        if not hasattr(self, "posture_log_path"):
            self.posture_log_path = os.path.join(LOG_DIR, time.strftime("posture_%Y%m%d.txt"))
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        reason = status.get("reason") or "ok"
        tilt = f"{status.get('tilt',0):.1f}"
        nod  = f"{status.get('nod',0):.1f}"
        line = f"{ts}\t{reason}\ttilt={tilt}\tnod={nod}\n"
        try:
            with open(self.posture_log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print("[PostureLog] erro:", e)

    def _log_posture_csv(self, status):
        self._maybe_reset_completed_counter()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        row = [
            ts,
            1 if status.get("ok") else 0,
            status.get("reason") or "",
            f"{status.get('tilt',0):.1f}",
            f"{status.get('nod',0):.1f}",
            getattr(self, "posture_adjust_count", 0),
            getattr(self, "tasks_completed_today", 0),
        ]
        try:
            with open(POSTURE_CSV, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(row)
        except Exception as e:
            print("[PostureCSV] erro:", e)
    def _ensure_camera(self):
        if not hasattr(self, "cam") or self.cam is None:
            from picamera2 import Picamera2
            self.cam = Picamera2()
            self.cam.configure(self.cam.create_still_configuration())
            self.cam.start()
            time.sleep(0.2)

    def run_posture_once(self):
        from sense_modes import RED, GREEN
        self._ensure_camera()
        frame = self.cam.capture_array()
        status = self.posture.analyze_frame(frame)

        # contador/log
        if not status.get("ok"):
            self.posture_adjust_count = getattr(self, "posture_adjust_count", 0) + 1
        self._log_posture_text(status)
        self._log_posture_csv(status)

        # LED
        self._flash(GREEN if status.get("ok") else RED, times=3)

        # salva último frame
        try:
            import cv2
            cv2.imwrite("/home/pi/pi_productivity/last_posture.jpg", frame)
        except Exception:
            pass

        self._show_mode_pattern(self.MODES[self.mode_index])
        return status

    def _iso_from_due_hint(self, due_hint):
        from datetime import datetime, timedelta, timezone
        if due_hint:
            try:
                d = datetime.fromisoformat(due_hint.strip())
                d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                return d.isoformat().replace("+00:00","Z")
            except Exception:
                pass
        d = datetime.utcnow() + timedelta(days=OCR_DEFAULT_DUE_DAYS)
        d = d.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        return d.isoformat().replace("+00:00","Z")

    def _ocr_parse_actions(self, text):
        """
        Seções com TÍTULO, e linhas de tarefas:
        - [ ] ...   ou   TODO: ...
        - [x] ...   ou   DONE: ...
        DUE: YYYY-MM-DD (opcional, afeta próximos TODO)
        """
        actions = []
        lines = [l.rstrip() for l in text.splitlines()]
        current_section = None
        pending_due = None

        def add_create(name):
            actions.append({"type":"create", "name":name.strip(), "due":pending_due, "section": current_section})

        def add_complete(name):
            actions.append({"type":"complete", "name":name.strip(), "section": current_section})

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            low = line.lower()

            if not line:
                i += 1; continue

            if low.startswith("due:"):
                pending_due = line.split(":",1)[1].strip()
                i += 1; continue

            if low.startswith("- [ ]"):
                name = line.split("]",1)[-1].strip()
                add_create(name); i += 1; continue

            if low.startswith("- [x]"):
                name = line.split("]",1)[-1].strip()
                add_complete(name); i += 1; continue

            if low.startswith("todo:"):
                name = line.split(":",1)[1].strip()
                add_create(name); i += 1; continue

            if low.startswith("done:"):
                name = line.split(":",1)[1].strip()
                add_complete(name); i += 1; continue

            # Se chegou aqui, tratamos como TÍTULO
            current_section = line.strip()
            pending_due = None
            i += 1

        return actions

    def _ocr_apply_to_motion(self, text):
        if not MOTION_ENABLE_OCR:
            print("[OCR→Motion] desabilitado (MOTION_ENABLE_OCR=0)")
            return
        try:
            from motion_client import MotionClient
            if not hasattr(self, "motion") or self.motion is None:
                self.motion = MotionClient()
        except Exception as e:
            print("[OCR→Motion] Motion indisponível:", e)
            return

        acts = self._ocr_parse_actions(text)
        if not acts:
            print("[OCR→Motion] nenhum comando reconhecido")
            return

        created = 0; completed = 0
        for a in acts:
            section = a.get("section") or ""
            try:
                if a["type"] == "create":
                    due_iso = self._iso_from_due_hint(a.get("due"))
                    self.motion.create_task(
                        name=a["name"], description="(via OCR)",
                        due_date_iso=due_iso,
                        labels=[section] if section else None
                    )
                    created += 1
                    self._log_task_event("create", section, a["name"])
                elif a["type"] == "complete":
                    t = self.motion.find_task_by_name(a["name"])
                    if t:
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
                    else:
                        t = self.motion.create_task(name=a["name"], description="(via OCR, auto-complete)",
                                                    labels=[section] if section else None)
                        self.motion.complete_task(t["id"])
                        completed += 1
                        self._log_task_event("complete", section, a["name"])
            except Exception as e:
                print("[OCR→Motion] erro:", e)

        print(f"[OCR→Motion] criadas={created} concluídas={completed}")

    def run_ocr_once(self):
        self._ensure_camera()
        frame = self.cam.capture_array()
        img_path, txt_path, text = self.ocr.capture_and_ocr(frame)

        # aciona Motion
        try:
            self._ocr_apply_to_motion(text)
        except Exception as e:
            print("[OCR→Motion] erro:", e)

        self._flash([0,255,255], times=3)  # ciano
        print(f"OCR salvo em: {txt_path}")
        self._show_mode_pattern(self.MODES[self.mode_index])
        return img_path, txt_path, text
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
            time.sleep(max(60, OCR_INTERVAL))

            
    def run(self):
        self._render_mode_banner()
        sense.stick.direction_any = self.handle_joystick
        while True:
            self.maybe_poll_motion()
            time.sleep(1)

if __name__ == "__main__":
    App().run()
