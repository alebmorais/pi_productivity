# camera_posture.py
from dataclasses import dataclass
import os
import cv2
import numpy as np

@dataclass
class PostureConfig:
    face_scale_factor: float = 1.1
    face_min_neighbors: int = 5
    tilt_thresh_deg: float = 12.0   # inclinação lateral (roll)
    nod_thresh_deg: float = 12.0    # inclinação frente/trás (pitch)

def _load_face_cascade():
    # Caminhos típicos no Debian/Raspberry Pi para os haarcascades
    candidates = [
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    ]
    for p in candidates:
        if os.path.exists(p):
            return cv2.CascadeClassifier(p)
    raise FileNotFoundError(
        "Não encontrei 'haarcascade_frontalface_default.xml' em /usr/share/opencv4/haarcascades"
    )

class PostureMonitor:
    def __init__(self, cfg: PostureConfig):
        self.cfg = cfg
        self.face_cascade = _load_face_cascade()

    def _estimate_angles_from_landmarks(self, gray, face_rect):
        # Simples heurística com bounding box: não é perfeito, mas leve.
        (x, y, w, h) = face_rect
        cx, cy = x + w / 2, y + h / 2
        # Medidas relativas para um "roll/pitch" aproximado
        roll = (cx - gray.shape[1] / 2) / gray.shape[1] * 40.0   # ~±20°
        pitch = (gray.shape[0] / 2 - cy) / gray.shape[0] * 40.0  # ~±20°
        return roll, pitch

    def analyze_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.cfg.face_scale_factor,
            minNeighbors=self.cfg.face_min_neighbors,
            minSize=(60, 60),
        )
        if len(faces) == 0:
            return {"ok": True, "reason": "face_not_found", "tilt": 0.0, "nod": 0.0}

        # pega a maior face
        faces = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)
        roll, pitch = self._estimate_angles_from_landmarks(gray, faces[0])

        need_adjust = abs(roll) > self.cfg.tilt_thresh_deg or abs(pitch) > self.cfg.nod_thresh_deg
        reason = "ok"
        if abs(roll) > self.cfg.tilt_thresh_deg:
            reason = "tilt"
        if abs(pitch) > self.cfg.nod_thresh_deg:
            reason = "nod" if reason == "ok" else (reason + "+nod")
        return {"ok": not need_adjust, "reason": reason, "tilt": float(roll), "nod": float(pitch)}
