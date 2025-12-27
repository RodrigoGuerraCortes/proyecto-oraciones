# generator/v2/video/title_renderer.py

from dataclasses import dataclass
import textwrap
import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ANCHO = 1080
ALTO = 1920


# ==========================================================
# Estilo de título
# ==========================================================
@dataclass
class TitleStyle:
    font_path: str = "DejaVuSerif-Bold.ttf"
    font_size: int = 70
    title_color: str = "#e4d08a"
    shadow_color: str = "black"
    line_spacing: int = 12
    max_width_chars: int = 18
    y: int = 120


# ==========================================================
# Diccionario de acentos (controlado, determinista)
# ==========================================================
ACCENT_MAP = {
    "oracion": "oración",
    "senor": "señor",
    "senora": "señora",
    "dios": "Dios",
    "jesus": "Jesús",
    "corazon": "corazón",
    "espiritu": "espíritu",
    "liberacion": "liberación",
    "proteccion": "protección",
    "misericordia": "misericordia",
    "agradecimiento": "agradecimiento",
}


MINOR_WORDS = {
    "de", "para", "el", "la", "los", "las",
    "y", "en", "al", "del", "un", "una",
    "por", "a"
}


# ==========================================================
# Normalización lingüística
# ==========================================================
def aplicar_acentos(texto: str) -> str:
    """
    Aplica reemplazos de acentos preservando signos y emojis.
    """
    palabras = texto.split()
    out = []

    for p in palabras:
        m = re.match(r"^(\W*)(\w+)(\W*)$", p, re.UNICODE)
        if not m:
            out.append(p)
            continue

        pre, core, post = m.groups()
        core_l = core.lower()

        if core_l in ACCENT_MAP:
            out.append(pre + ACCENT_MAP[core_l] + post)
        else:
            out.append(p)

    return " ".join(out)


def title_case_es(texto: str) -> str:
    """
    Capitaliza según reglas básicas del español.
    """
    palabras = texto.split()
    out = []

    for i, p in enumerate(palabras):
        pl = p.lower()

        if i == 0 or pl not in MINOR_WORDS:
            out.append(pl[:1].upper() + pl[1:])
        else:
            out.append(pl)

    return " ".join(out)


def normalize_title(text: str) -> str:
    """
    Normaliza título completo:
    - aplica acentos
    - capitaliza correctamente
    """
    text = aplicar_acentos(text)
    text = title_case_es(text)
    return text


# ==========================================================
# Renderer
# ==========================================================
def render_title_layer(
    *,
    title: str,
    output_path: str,
    style: TitleStyle,
):
    """
    Renderiza el TÍTULO como una CAPA PNG COMPLETA (1080x1920).
    Centrado horizontalmente, Y fija.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.font_size)
    except Exception:
        font = ImageFont.load_default()

    normalized = normalize_title(title)

    lines = textwrap.wrap(
        normalized,
        width=style.max_width_chars,
        break_long_words=False,
    )

    print(f"[TitleRenderer] Title: {normalized}")
    print(f"[TitleRenderer] Split in {len(lines)} lines.")

    y = style.y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        # sombra
        for dx, dy in [
            (-3, 0), (3, 0), (0, -3), (0, 3),
            (-3, -3), (3, -3), (-3, 3), (3, 3),
        ]:
            draw.text((x + dx, y + dy), line, font=font, fill=style.shadow_color)

        draw.text((x, y), line, font=font, fill=style.title_color)
        y += h + style.line_spacing

    img.save(output_path)
