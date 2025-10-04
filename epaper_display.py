"""Helpers to render content on the Waveshare e-paper display.

The class is purposely lightweight so it can also be used in unit tests
or when running on a machine without the hardware attached.  When no
physical display is detected the generated PNG is written to
``/mnt/data/pi_productivity/last_epaper.png`` by default so the caller
can inspect the output.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Sequence

from PIL import Image, ImageDraw, ImageFont

from task_database import TaskDatabase

EPD_W, EPD_H = 200, 200
DEFAULT_OUTPUT_PATH = Path(
    os.getenv("EPAPER_OUTPUT_PATH", "/mnt/data/pi_productivity/last_epaper.png")
).expanduser()


def load_font(size: int = 14) -> ImageFont.FreeTypeFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


class EPaperDisplay:
    def __init__(self, rotate_180: bool = False, output_path: Path | str | None = None):
        self.rotate_180 = rotate_180
        self.font = load_font(14)
        self.font_small = load_font(12)
        self.output_path = Path(output_path).expanduser() if output_path else DEFAULT_OUTPUT_PATH

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def render_list(self, items: Sequence[Dict[str, str]], title: str = "Tarefas do Dia") -> Path:
        img = Image.new("1", (EPD_W, EPD_H), 1)
        draw = ImageDraw.Draw(img)
        y = 4
        draw.text((6, y), title[:20], font=self.font, fill=0)
        y += 18
        draw.line((6, y, EPD_W - 6, y), fill=0)
        y += 4
        for item in list(items)[:6]:
            left = str(item.get("title", ""))
            right = str(item.get("right", ""))
            subtitle = str(item.get("subtitle", ""))
            draw.text((6, y), left[:22], font=self.font_small, fill=0)
            if right:
                width = draw.textlength(right, font=self.font_small)
                draw.text((EPD_W - 6 - width, y), right[:10], font=self.font_small, fill=0)
            y += 14
            if subtitle:
                draw.text((10, y), f"• {subtitle[:24]}", font=self.font_small, fill=0)
                y += 12
            y += 2
        return self.push_to_hardware(img)

    def render_tip(self, tip: str, title: str = "Estudo (TDAH)") -> Path:
        img = Image.new("1", (EPD_W, EPD_H), 1)
        draw = ImageDraw.Draw(img)
        y = 4
        draw.text((6, y), title[:20], font=self.font, fill=0)
        y += 18
        draw.line((6, y, EPD_W - 6, y), fill=0)
        y += 6
        wrap: List[str] = []
        line = ""
        for word in tip.split():
            if len(line) + len(word) + 1 > 22:
                wrap.append(line)
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            wrap.append(line)
        for entry in wrap[:10]:
            draw.text((8, y), entry, font=self.font_small, fill=0)
            y += 14
        return self.push_to_hardware(img)

    def render_tasks_from_database(
        self,
        db_path: Path | str | None = None,
        title: str = "Tarefas do Dia",
        limit: int = 6,
    ) -> Path:
        database = TaskDatabase(db_path)
        items = database.fetch_items_for_display(limit=limit)
        return self.render_list(items, title=title)

    # ------------------------------------------------------------------
    # Output helper
    # ------------------------------------------------------------------
    def push_to_hardware(self, image: Image.Image) -> Path:
        if self.rotate_180:
            image = image.rotate(180)
        output = self.output_path
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza o display e-paper com dados do banco de tarefas.")
    parser.add_argument("--db", dest="db_path", help="Caminho para o banco SQLite", default=None)
    parser.add_argument("--title", dest="title", help="Título mostrado no display", default="Tarefas do Dia")
    parser.add_argument("--limit", dest="limit", type=int, default=6, help="Número máximo de itens exibidos")
    parser.add_argument("--rotate-180", dest="rotate", action="store_true", help="Gira a imagem 180° antes de salvar")
    parser.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Sobrescreve o caminho padrão do arquivo PNG gerado",
    )
    args = parser.parse_args()

    display = EPaperDisplay(rotate_180=args.rotate, output_path=args.output)
    path = display.render_tasks_from_database(db_path=args.db_path, title=args.title, limit=args.limit)
    print(path)


if __name__ == "__main__":  # pragma: no cover
    main()
