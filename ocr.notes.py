# ocr_notes.py
from dataclasses import dataclass
from pathlib import Path
import os, time
import cv2
import pytesseract

@dataclass
class OCRConfig:
    output_dir: str = os.path.expanduser("~/pi_productivity/notes")

class OCRNotes:
    def __init__(self, cfg: OCRConfig):
        self.cfg = cfg
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

    def _preprocess(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3,3), 0)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
        return gray

    def capture_and_ocr(self, frame):
        img = self._preprocess(frame)
        ts = time.strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(self.cfg.output_dir, f"note_{ts}.png")
        txt_path = os.path.join(self.cfg.output_dir, f"note_{ts}.txt")
        cv2.imwrite(img_path, img)
        text = pytesseract.image_to_string(img, lang="eng")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return img_path, txt_path, text
