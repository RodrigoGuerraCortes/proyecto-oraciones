# generator/v2/video/text_renderer.py

from dataclasses import dataclass
from typing import List

from PIL import Image, ImageDraw, ImageFont
from click import style


ANCHO = 1080
ALTO = 1920


@dataclass
class TextStyle:
    font_path: str = "DejaVuSans.ttf"
    base_size: int = 82
    color: tuple = (255, 255, 255, 255)
    shadow_color: tuple = (0, 0, 0, 255)
    max_width: int = 980
    line_spacing: int = 22


def render_text_block(
    *,
    lines: List[str],
    output_path: str,
    style: TextStyle,
):
    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.base_size)
    except Exception:
        font = ImageFont.load_default()

    try:
        bbox = font.getbbox("A")
        h_line = bbox[3] - bbox[1]
    except Exception:
        h_line = style.base_size

    total_h = len(lines) * (h_line + style.line_spacing)
    y = (ALTO - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        for dx, dy in [(-4,-4),(4,-4),(4,4),(-4,4)]:
            draw.text((x+dx, y+dy), line, font=font, fill=style.shadow_color)

        draw.text((x, y), line, font=font, fill=style.color)
        y += h + style.line_spacing

    img.save(output_path)
