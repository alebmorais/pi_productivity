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

    def run(self):
        self._render_mode_banner()
        sense.stick.direction_any = self.handle_joystick
        while True:
            self.maybe_poll_motion()
            time.sleep(1)

if __name__ == "__main__":
    App().run()
