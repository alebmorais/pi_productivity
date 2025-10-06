from dataclasses import dataclass
import cv2, os, math

@dataclass
class PostureConfig:
    tilt_threshold_deg: float = 12.0
    nod_threshold_deg: float = 12.0

class PostureMonitor:
    def __init__(self, cfg: PostureConfig):
        self.cfg = cfg
        # Caminhos Debian/RPi para cascatas
        candidates = [
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
        ]
        cascade_path = next((p for p in candidates if os.path.exists(p)), None)
        if not cascade_path:
            raise FileNotFoundError("Não encontrei haarcascade_frontalface_default.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def analyze_frame(self, frame):
        status = {"ok": True, "reason": "ok", "tilt": 0.0, "nod": 0.0}

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
            if len(faces) == 0:
                status["ok"] = False
                status["reason"] = "sem_face"
        except Exception:
            pass
        return status
