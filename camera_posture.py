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

        eye_candidates = [
            "/usr/share/opencv4/haarcascades/haarcascade_eye.xml",
            "/usr/share/opencv/haarcascades/haarcascade_eye.xml",
        ]
        eye_cascade_path = next((p for p in eye_candidates if os.path.exists(p)), None)
        if not eye_cascade_path:
            raise FileNotFoundError("Não encontrei haarcascade_eye.xml")
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    def analyze_frame(self, frame):
        status = {"ok": True, "reason": "ok", "tilt": 0.0, "nod": 0.0}

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            status.update({"ok": False, "reason": "frame_invalido"})
            return status

        gray = cv2.equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        if len(faces) == 0:
            status.update({"ok": False, "reason": "sem_face"})
            return status

        # Escolhe o maior rosto (caso existam vários)
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi_gray = gray[y : y + h, x : x + w]

        eyes = self.eye_cascade.detectMultiScale(
            face_roi_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(max(10, w // 10), max(10, h // 10)),
        )

        if len(eyes) < 2:
            status.update({"ok": False, "reason": "olhos_nao_detectados"})
            return status

        # Seleciona os dois olhos mais largos
        eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
        eye_centers = []
        for (ex, ey, ew, eh) in eyes:
            cx = ex + ew / 2.0
            cy = ey + eh / 2.0
            eye_centers.append((cx, cy))

        # Ordena por posição horizontal (olho esquerdo e direito)
        eye_centers.sort(key=lambda c: c[0])
        (left_x, left_y), (right_x, right_y) = eye_centers

        dx = right_x - left_x
        dy = right_y - left_y
        if dx == 0:
            tilt_angle = 0.0
        else:
            tilt_angle = math.degrees(math.atan2(dy, dx))

        # Heurística simples para o ângulo de nod (pitch)
        eyes_center_y = (left_y + right_y) / 2.0
        normalized_offset = (eyes_center_y / float(h)) - 0.5
        nod_angle = normalized_offset * 90.0  # escala heurística

        status["tilt"] = float(tilt_angle)
        status["nod"] = float(nod_angle)

        reasons = []
        if abs(tilt_angle) > self.cfg.tilt_threshold_deg:
            reasons.append("tilt_excedido")
        if abs(nod_angle) > self.cfg.nod_threshold_deg:
            reasons.append("nod_excedido")

        if reasons:
            status["ok"] = False
            status["reason"] = ";".join(reasons)

        return status
