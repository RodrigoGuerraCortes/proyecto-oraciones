# generator/v2/video/text_renderer.py

from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

ANCHO = 1080
ALTO = 1920


@dataclass
class TextStyle:
    font_path: str
    font_size: int
    color: str = "white"
    shadow_color: str = "black"
    line_spacing: int = 18
    max_width_px: int = 820
    outline_px: int = 2
    outline_color: str = "black"


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

    print(
        "[DEBUG][TEXT_STYLE]",
        {
            "font_path": style.font_path,
            "font_size": style.font_size,
            "line_spacing": style.line_spacing,
            "max_width_px": style.max_width_px,
            "y_start": y_start,
            "lines_count": len(lines),
        }
    )


    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(style.font_path, style.font_size)
    except Exception as e:
        raise RuntimeError(f"[TEXT] Font load failed: {style.font_path}") from e

    wrapped: list[str] = []

    for line in lines:
        words = line.split()
        current = ""

        for word in words:
            test = current + (" " if current else "") + word
            w = draw.textlength(test, font=font)

            if w <= style.max_width_px:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = word

        if current:
            wrapped.append(current)


    if not wrapped:
        wrapped = [""]  # evita render vacío

    bbox = draw.textbbox((0, 0), "A", font=font)
    line_h = bbox[3] - bbox[1]
    total_h = len(wrapped) * line_h + (len(wrapped) - 1) * style.line_spacing

    y = y_start
    block_x = (ANCHO - style.max_width_px) // 2

    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = block_x + (style.max_width_px - w) // 2

        # ==========================
        # CONTORNO REAL (configurable)
        # ==========================
        if style.outline_px > 0:
            o = style.outline_px
            outline_offsets = [
                (-o, 0), (o, 0), (0, -o), (0, o),
                (-o, -o), (o, -o), (-o, o), (o, o),
            ]

            for dx, dy in outline_offsets:
                draw.text(
                    (x + dx, y + dy),
                    line,
                    font=font,
                    fill=style.outline_color,
                )


        # ==========================
        # TEXTO PRINCIPAL
        # ==========================
        draw.text(
            (x, y),
            line,
            font=font,
            fill=style.color,
        )

        y += line_h + style.line_spacing + 4

    img.save(output_path)

    print(
        "[DEBUG][TEXT_WRAP]",
        {
            "wrapped_lines": len(wrapped),
            "total_height": total_h,
        }
    )


    # DEBUG DURO
    if not output_path.exists():
        raise RuntimeError(f"[TEXT] PNG not written: {output_path}")
