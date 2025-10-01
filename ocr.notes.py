from dataclasses import dataclass
from pathlib import Path
import os, cv2, pytesseract, time

@dataclass
class OCRConfig:
    output_dir: str = os.path.expanduser("~/pi_productivity/notes")

class OCRNotes:
    def __init__(self, cfg: OCRConfig):
        self.cfg = cfg
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

    def _ts(self):
        return time.strftime("%Y%m%d_%H%M%S")

    def capture_and_ocr(self, frame):
        # Pré-processamento simples
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3,3), 0)
        _, thr = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY)

        base = f"note_{self._ts()}"
        img_path = os.path.join(self.cfg.output_dir, f"{base}.png")
        txt_path = os.path.join(self.cfg.output_dir, f"{base}.txt")
        cv2.imwrite(img_path, thr)

        # OCR
        text = pytesseract.image_to_string(thr, lang="eng")  # ajuste idiomas se quiser
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        return img_path, txt_path, text
