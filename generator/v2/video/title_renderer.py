# generator/v2/video/title_renderer.py

from dataclasses import dataclass
from typing import List
import textwrap

from PIL import Image, ImageDraw, ImageFont


ANCHO = 1080


@dataclass
class TitleStyle:
    font_path: str = "DejaVuSerif-Bold.ttf"
    font_size: int = 70
    text_color: str = "#e4d08a"
    shadow_color: str = "black"
    line_spacing: int = 12
    max_width_chars: int = 18


def split_title_lines(title: str, max_width: int) -> List[str]:
    return textwrap.wrap(title, width=max_width)


def render_title_image(
    *,
    title: str,
    output_path: str,
    style: TitleStyle,
):
    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.font_size)
    except Exception:
        font = ImageFont.load_default()

    lines = split_title_lines(title, style.max_width_chars)

    y = 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        # sombra
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3)]:
            draw.text((x+dx, y+dy), line, font=font, fill=style.shadow_color)

        draw.text((x, y), line, font=font, fill=style.text_color)
        y += h + style.line_spacing

    img.save(output_path)
