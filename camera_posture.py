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

        # Cascade para olhos
        eye_cascade_candidates = [
            "/usr/share/opencv4/haarcascades/haarcascade_eye.xml",
            "/usr/share/opencv/haarcascades/haarcascade_eye.xml",
        ]
        eye_cascade_path = next((p for p in eye_cascade_candidates if os.path.exists(p)), None)
        if not eye_cascade_path:
            raise FileNotFoundError("Não encontrei haarcascade_eye.xml")
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

    def _get_eye_angle(self, face_roi_gray):
        import numpy as np
        eyes = self.eye_cascade.detectMultiScale(face_roi_gray, 1.1, 5)
        if len(eyes) < 2:
            return 0.0

        # Pega os dois maiores olhos e calcula o centro
        eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
        
        # Garante que os olhos estão em posições razoáveis (um à esquerda, um à direita)
        centers = [(e[0] + e[2] // 2, e[1] + e[3] // 2) for e in eyes]
        if centers[0][0] > centers[1][0]:
            centers = (centers[1], centers[0])

        (x1, y1), (x2, y2) = centers
        
        # Evita divisão por zero
        if x2 - x1 == 0:
            return 90.0 if y2 > y1 else -90.0
            
        angle_rad = np.arctan2(y2 - y1, x2 - x1)
        return np.degrees(angle_rad)

    def analyze_frame(self, frame):
        status = {"ok": True, "reason": "ok", "tilt": 0.0, "nod": 0.0}
        try:
            if frame is None:
                status["ok"] = False
                status["reason"] = "no_frame"
                return status

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)

            if len(faces) == 0:
                status["ok"] = False
                status["reason"] = "sem_face"
                return status

            # Pega a maior face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face_roi_gray = gray[y:y+h, x:x+w]

            # 1. Tilt (inclinação lateral)
            tilt = self._get_eye_angle(face_roi_gray)
            status["tilt"] = tilt
            if abs(tilt) > self.cfg.tilt_threshold_deg:
                status["ok"] = False
                status["reason"] = "tilt"

            # 2. Nod (inclinação vertical) - heurística simples
            # Se o centro da face está muito acima/abaixo do centro da imagem
            frame_h, _, = frame.shape[:2]
            face_center_y = y + h / 2
            # Mapeia a posição vertical para um ângulo aproximado
            nod = (frame_h / 2 - face_center_y) / (frame_h / 2) * 45 
            status["nod"] = nod
            if abs(nod) > self.cfg.nod_threshold_deg:
                status["ok"] = False
                # Prioriza o tilt no motivo do erro
                if status["reason"] == "ok":
                    status["reason"] = "nod"
            
        except Exception as e:
            status["ok"] = False
            status["reason"] = f"error: {e}"
            
        return status
