"""
FASE A — Render de capas de texto del Tractor

Objetivo:
- Leer todos los TXT definidos en content.blocks
- Dividir cada TXT en bloques lógicos (\n\n)
- Renderizar cada bloque como una imagen PNG independiente
- No generar video
- No usar MoviePy
- No usar TTS
"""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap
import sys


# -------------------------------------------------
# Configuración base (hardcodeada a propósito)
# -------------------------------------------------
WIDTH = 1920
HEIGHT = 1080

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SIZE = 56

TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0, 0)  # negro sólido

MARGIN_X = 200
LINE_SPACING = 12

TEXT_PANEL_LEFT = int(WIDTH * 0.55)
TEXT_PANEL_RIGHT = WIDTH - 200
TEXT_PANEL_WIDTH = TEXT_PANEL_RIGHT - TEXT_PANEL_LEFT


# -------------------------------------------------
# Utilidad: renderizar texto en una imagen
# -------------------------------------------------
def render_text_to_image(text: str, output_path: str) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    lines = []

    for paragraph in text.split("\n"):
        wrapped = wrap_text_by_width(
            paragraph,
            font,
            TEXT_PANEL_WIDTH
        )
        lines.extend(wrapped)


    #MAX_LINES = 4
    #if len(lines) > MAX_LINES:
    #    lines = lines[:MAX_LINES]

    line_height = font.getbbox("Ay")[3] + LINE_SPACING
    total_text_height = len(lines) * line_height

    BOTTOM_MARGIN = 220
    y = HEIGHT - total_text_height - BOTTOM_MARGIN

    # -------------------------------
    # Ajuste progresivo para textos cortos
    # -------------------------------
    MAX_LINES = 10          # referencia visual (lo que se ve "bien")
    MIN_LINES = 2

    if len(lines) < MAX_LINES:
        missing_lines = MAX_LINES - len(lines)

        # cuánto subir por cada línea faltante
        SHIFT_PER_LINE = int(line_height * 0.6)

        shift_up = missing_lines * SHIFT_PER_LINE
        y -= shift_up

        print(
            f"[TEXT-LAYER] SHORT ADJUST:"
            f" lines={len(lines)}"
            f" missing={missing_lines}"
            f" shift_up={shift_up}"
            f" y_adjusted={y}"
        )
    else:
        print("[TEXT-LAYER] NO SHORT ADJUST")
        
    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = TEXT_PANEL_LEFT + int((TEXT_PANEL_WIDTH - text_width) / 2)
        draw.text(
            (x, y),
            line,
            font=font,
            fill=TEXT_COLOR,
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255),
        )
        y += line_height

    return img


# -------------------------------------------------
# Entrada principal
# -------------------------------------------------
def render_layers_from_config(resolved_config: dict):
    content_cfg = resolved_config["content"]
    base_path = content_cfg["base_path"]
    blocks = content_cfg["blocks"]
    output_path = content_cfg["layers_path"]
    os.makedirs(output_path, exist_ok=True)

    index = 1

    print("[TRACTOR][LAYERS] Renderizando capas de texto...")

    print("[TRACTOR][LAYERS] Output base:", output_path)
    print("[TRACTOR][LAYERS] Base path:", base_path)
    print("[TRACTOR][LAYERS] Bloques:", blocks)


    for block_file in blocks:
        txt_path = os.path.join(base_path, block_file)

        if not os.path.exists(txt_path):
            raise FileNotFoundError(txt_path)

        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        sub_blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

        print(
            f"[TRACTOR][LAYERS] {block_file}: {len(sub_blocks)} sub-bloques"
        )

        for sub_idx, block_text in enumerate(sub_blocks, start=1):
            img = render_text_to_image(block_text, output_path)

            filename = (
                f"{index:04d}_"
                f"{block_file.replace('.txt','')}_"
                f"{sub_idx:02d}.png"
            )

            output_path_png = os.path.join(output_path, filename)
            img.save(output_path_png, format="PNG")

            print("  ✔", output_path_png)
            index += 1

    print("[TRACTOR][LAYERS] Render finalizado")
    print("[TRACTOR][LAYERS] Total capas:", index - 1)

def wrap_text_by_width(text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        w = font.getbbox(test)[2]
        if w <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines

# -------------------------------------------------
# Uso desde entrypoint / test manual
# -------------------------------------------------
if __name__ == "__main__":
    raise RuntimeError(
        "Este script debe ejecutarse desde el pipeline "
        "pasándole resolved_config explícitamente"
    )
