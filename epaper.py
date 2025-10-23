import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Attempt to import the real EPD library.
# The Waveshare driver may attempt to claim GPIO pins at import time and
# raise low-level errors (e.g. lgpio.error 'GPIO busy').
# Catch any Exception here and fall back to a mock implementation so the
# web server can run even if the display (or GPIO) is unavailable.
try:
    from waveshare_epd import epd1in54_V2  # type: ignore
    EPD_AVAILABLE = True
except Exception as e:  # Broad catch: ImportError, RuntimeError, lgpio.error, etc.
    EPD_AVAILABLE = False
    print(f"Warning: waveshare_epd import failed or unavailable: {e}")

class EPD:
    """A wrapper for the e-paper display, with a mock for non-Pi development."""

    def __init__(self, output_dir: str = "~/pi_productivity/analytics"):
        self.output_dir = Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if EPD_AVAILABLE:
            self.epd = epd1in54_V2.EPD()
            self.width = self.epd.width
            self.height = self.epd.height
        else:
            self.epd = None
            self.width = 200
            self.height = 200
            print("Warning: E-Paper display not found. Mock images will be generated.")

    def _init_display(self):
        if self.epd:
            self.epd.init()
            self.epd.Clear()

    def _display_image(self, image):
        if self.epd:
            self.epd.display(self.epd.getbuffer(image))
            self.epd.sleep()
        else:
            # Save as a mock image if no display is present
            path = self.output_dir / "epaper_mock.png"
            image.save(path)
            return str(path)
        return None

    def render_list(self, items: list[dict], title: str = "Tasks") -> str | None:
        """Renders a list of items to the display."""
        image = Image.new('1', (self.width, self.height), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(image)
        
        try:
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            title_font = ImageFont.truetype(font_path, 18)
            item_font = ImageFont.truetype(font_path.replace("-Bold", ""), 14)
        except IOError:
            title_font = ImageFont.load_default()
            item_font = ImageFont.load_default()

        # Title
        draw.text((10, 5), title, font=title_font, fill=0)
        draw.line([(10, 30), (self.width - 10, 30)], fill=0)

        # Items
        y = 35
        for item in items[:6]:  # Limit items to fit
            title_text = item.get("title", "No Title")
            draw.text((10, y), f"- {title_text[:30]}", font=item_font, fill=0)
            y += 20
        
        self._init_display()
        return self._display_image(image)

    def render_tip(self, tip: str, title: str = "Info") -> str | None:
        """Renders a simple tip or message."""
        items = [{"title": line} for line in tip.split('\n')]
        return self.render_list(items, title=title)
