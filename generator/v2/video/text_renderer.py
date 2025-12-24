# generator/v2/video/text_renderer.py

from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

ANCHO = 1080
ALTO = 1920


@dataclass
class TextStyle:
    font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    size_large: int = 54
    color: str = "white"
    shadow_color: str = "black"
    line_spacing: int = 14
    max_width_chars: int = 32


def render_text_layer(
    *,
    lines: list[str],
    output_path: str,
    style: TextStyle,
    y_start: int = 360,
):
    """
    Renderiza el TEXTO como una CAPA PNG 1080x1920.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.size_large)
    except Exception as e:
        raise RuntimeError(f"[TEXT] Font load failed: {style.font_path}") from e

    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=style.max_width_chars))

    if not wrapped:
        wrapped = [""]  # evita render vacío

    bbox = draw.textbbox((0, 0), "A", font=font)
    line_h = bbox[3] - bbox[1]
    total_h = len(wrapped) * (line_h + style.line_spacing)

    y = y_start + (ALTO - y_start - total_h) // 2

    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (ANCHO - w) // 2

        # sombra
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
            draw.text((x + dx, y + dy), line, font=font, fill=style.shadow_color)

        draw.text(
            (x, y),
            line,
            font=font,
            fill=style.color,
            stroke_width=3,
            stroke_fill="black",
        )

        y += line_h + style.line_spacing

    img.save(output_path)

    # DEBUG DURO
    if not output_path.exists():
        raise RuntimeError(f"[TEXT] PNG not written: {output_path}")
