
import os, cv2, pytesseract
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class OCRConfig:
    output_dir: str = "/mnt/data/pi_productivity/notes"
    dpi: int = 300
    lang: str = "por+eng"
    blur: int = 3

class OCRNotes:
    def __init__(self, cfg: OCRConfig|None=None):
        self.cfg = cfg or OCRConfig()
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

    def preprocess(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, self.cfg.blur)
        bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 15)
        return bw

    def capture_and_ocr(self, frame_bgr):
        bw = self.preprocess(frame_bgr)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(self.cfg.output_dir, f"note_{ts}.png")
        txt_path = os.path.join(self.cfg.output_dir, f"note_{ts}.txt")
        cv2.imwrite(img_path, bw)
        config = f"--oem 1 --psm 6 -l {self.cfg.lang}"
        text = pytesseract.image_to_string(bw, config=config)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return img_path, txt_path, text
