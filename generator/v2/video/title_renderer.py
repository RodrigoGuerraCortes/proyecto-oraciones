# generator/v2/video/title_renderer.py

from dataclasses import dataclass
import textwrap
from PIL import Image, ImageDraw, ImageFont

ANCHO = 1080
ALTO = 1920


@dataclass
class TitleStyle:
    font_path: str = "DejaVuSerif-Bold.ttf"
    font_size: int = 70
    title_color: str = "#e4d08a"
    shadow_color: str = "black"
    line_spacing: int = 12
    max_width_chars: int = 18
    y: int = 120


def render_title_layer(
    *,
    title: str,
    output_path: str,
    style: TitleStyle,
):
    """
    Renderiza el TÍTULO como una CAPA PNG COMPLETA (1080x1920).
    Centrado horizontalmente, y en Y fija (V1).
    """
    from pathlib import Path

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.font_size)
    except Exception:
        font = ImageFont.load_default()



    lines = textwrap.wrap(normalize_title(title), width=style.max_width_chars)

    y = style.y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        for dx, dy in [
            (-3, 0), (3, 0), (0, -3), (0, 3),
            (-3, -3), (3, -3), (-3, 3), (3, 3),
        ]:
            draw.text((x + dx, y + dy), line, font=font, fill=style.shadow_color)

        draw.text((x, y), line, font=font, fill=style.title_color)
        y += h + style.line_spacing

    # 🔴 ESTO FALTABA
    img.save(output_path)


MINOR_WORDS = {
    "de", "para", "el", "la", "los", "las",
    "y", "en", "al", "del", "un", "una"
}

def normalize_title(text: str) -> str:
    words = text.strip().split()
    if not words:
        return text

    result = []

    for i, w in enumerate(words):
        lw = w.lower()

        if i == 0:
            # Solo la primera palabra se capitaliza
            result.append(lw[:1].upper() + lw[1:])
        elif lw in MINOR_WORDS:
            result.append(lw)
        else:
            # Mantiene tildes y mayúscula inicial
            result.append(lw[:1].upper() + lw[1:])

    return " ".join(result)
