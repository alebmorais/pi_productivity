
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict
import os

EPD_W, EPD_H = 200, 200

def load_font(size=14):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

class EPaperDisplay:
    def __init__(self, rotate_180=False):
        self.rotate_180 = rotate_180
        self.font = load_font(14)
        self.font_small = load_font(12)

    def render_list(self, items: List[Dict[str,str]], title="Tarefas do Dia"):
        img = Image.new("1", (EPD_W, EPD_H), 1)
        d = ImageDraw.Draw(img)
        y = 4
        d.text((6, y), title[:20], font=self.font, fill=0); y += 18
        d.line((6, y, EPD_W-6, y), fill=0); y += 4
        for it in items[:6]:
            left = it.get("title","")
            right = it.get("right","")
            sub = it.get("subtitle","")
            d.text((6, y), left, font=self.font_small, fill=0)
            if right:
                w = d.textlength(right, font=self.font_small)
                d.text((EPD_W-6-w, y), right, font=self.font_small, fill=0)
            y += 14
            if sub:
                d.text((10, y), f"• {sub}", font=self.font_small, fill=0)
                y += 12
            y += 2
        return self.push_to_hardware(img)

    def render_tip(self, tip:str, title="Estudo (TDAH)"):
        img = Image.new("1",(EPD_W,EPD_H),1)
        d = ImageDraw.Draw(img)
        y=4
        d.text((6,y), title[:20], font=self.font, fill=0); y+=18
        d.line((6,y,EPD_W-6,y), fill=0); y+=6
        wrap = []
        line = ""
        for word in tip.split():
            if len(line)+len(word)+1 > 22:
                wrap.append(line); line=word
            else:
                line = (line+" "+word).strip()
        if line: wrap.append(line)
        for l in wrap[:10]:
            d.text((8,y), l, font=self.font_small, fill=0); y+=14
        return self.push_to_hardware(img)

    def push_to_hardware(self, image):
        if self.rotate_180:
            image = image.rotate(180)
        out = "/mnt/data/pi_productivity/last_epaper.png"
        image.save(out)
        return out
