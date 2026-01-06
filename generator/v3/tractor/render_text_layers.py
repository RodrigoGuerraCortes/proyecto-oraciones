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

OUTPUT_BASE = "/mnt/storage/generated/tractor_layers"


# -------------------------------------------------
# Utilidad: renderizar texto en una imagen
# -------------------------------------------------
def render_text_to_image(text: str) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    max_chars_per_line = 60
    lines = []

    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=max_chars_per_line)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
        lines.append("")

    line_height = font.getbbox("Ay")[3] + LINE_SPACING
    total_text_height = len(lines) * line_height
    y = int((HEIGHT - total_text_height) / 2)

    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = int((WIDTH - text_width) / 2)
        draw.text((x, y), line, font=font, fill=TEXT_COLOR,stroke_width=3, stroke_fill=(0,0,0,255))
        y += line_height

    return img


# -------------------------------------------------
# Entrada principal
# -------------------------------------------------
def render_layers_from_config(resolved_config: dict):
    content_cfg = resolved_config["content"]
    base_path = content_cfg["base_path"]
    blocks = content_cfg["blocks"]

    os.makedirs(OUTPUT_BASE, exist_ok=True)

    index = 1

    print("[TRACTOR][LAYERS] Renderizando capas de texto...")
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
            img = render_text_to_image(block_text)

            filename = (
                f"{index:04d}_"
                f"{block_file.replace('.txt','')}_"
                f"{sub_idx:02d}.png"
            )

            output_path = os.path.join(OUTPUT_BASE, filename)
            img.save(output_path, format="PNG")

            print("  ✔", output_path)
            index += 1

    print("[TRACTOR][LAYERS] Render finalizado")
    print("[TRACTOR][LAYERS] Total capas:", index - 1)


# -------------------------------------------------
# Uso desde entrypoint / test manual
# -------------------------------------------------
if __name__ == "__main__":
    raise RuntimeError(
        "Este script debe ejecutarse desde el pipeline "
        "pasándole resolved_config explícitamente"
    )
