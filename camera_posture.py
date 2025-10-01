import time, math, cv2
from dataclasses import dataclass

@dataclass
class PostureConfig:
    frame_width: int = 640
    frame_height: int = 480
    min_face_size: int = 80
    max_tilt_deg: float = 20.0
    max_nod_deg: float = 20.0
    slouch_close_ratio: float = 0.33
    stable_seconds: float = 2.0

class PostureMonitor:
    def __init__(self, config: PostureConfig|None=None):
        self.cfg = config or PostureConfig()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.bad_since = None

    def _estimate_angles(self, face_rect, frame):
        (x,y,w,h) = face_rect
        roi = frame[y:y+h, x:x+w]
        if roi.size == 0:
            return 0.0, 0.0
        gx = cv2.Sobel(roi, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(roi, cv2.CV_32F, 0, 1, ksize=3)
        import math
        angle = math.degrees(math.atan2(gy.mean() + 1e-6, gx.mean() + 1e-6))
        tilt = max(min(angle, 90.0), -90.0)
        nod = math.degrees(math.atan2(h, w)) - 45.0
        return tilt, nod

    def analyze_frame(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(self.cfg.min_face_size, self.cfg.min_face_size))
        status = {"ok": True, "reason": None, "tilt": 0.0, "nod": 0.0, "faces": len(faces)}
        if len(faces) == 0:
            status["ok"] = False
            status["reason"] = "face_not_found"
            return status
        faces = sorted(faces, key=lambda r: r[2]*r[3], reverse=True)
        (x,y,w,h) = faces[0]
        tilt, nod = self._estimate_angles((x,y,w,h), gray)
        status["tilt"] = tilt
        status["nod"] = nod
        too_close = h >= self.cfg.frame_height * self.cfg.slouch_close_ratio
        bad_tilt = abs(tilt) > self.cfg.max_tilt_deg
        bad_nod  = abs(nod)  > self.cfg.max_nod_deg
        if too_close or bad_tilt or bad_nod:
            status["ok"] = False
            status["reason"] = "too_close" if too_close else ("tilt" if bad_tilt else "nod")
        return status
