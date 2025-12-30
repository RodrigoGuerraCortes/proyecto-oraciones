# generator/v2/content/layout/plain_layout.py

from generator.v2.content.layout.segmentation import dividir_en_bloques_por_lineas
from generator.v2.content.layout.duration import calcular_duracion_bloque
from generator.v2.content.parser import ParsedContent


def layout_plain(
    *,
    parsed: ParsedContent,
    content_cfg: dict,
    text_style,
    tts_enabled: bool = False,
    ):

    """
    plain:
      - parser entrega 1 bloque lógico
      - layout lo divide en sub-bloques visuales por líneas/ancho
      - calcula duración sugerida por bloque visual
    """
    if len(parsed.blocks) != 1:
        raise ValueError("plain espera exactamente 1 bloque lógico")

    block = parsed.blocks[0]

    max_lineas = content_cfg.get("max_lines", 14)

    textos = dividir_en_bloques_por_lineas(
        texto=block.text,
        font_path=text_style.font_path,
        font_size=text_style.font_size,
        max_width_px=text_style.max_width_px,
        max_lineas=max_lineas,
    )

    visual_blocks = []
    for texto in textos:
        visual_blocks.append(
            {
                "text": texto,
                "duration": float(
                    calcular_duracion_bloque(
                        texto,
                        tts_enabled=tts_enabled,
                    )
                ),
            }
        )

    # -----------------------------------
    # Ajuste por duración real de TTS
    # -----------------------------------
    tts_duration = content_cfg.get("_tts_duration")

    if tts_enabled and tts_duration and tts_duration > 0:
        total_visual = sum(b["duration"] for b in visual_blocks)

        if total_visual > 0:
            scale = tts_duration / total_visual

            for b in visual_blocks:
                b["duration"] *= scale

        print(
            "[LAYOUT][TTS-SCALE] "
            f"tts={tts_duration:.2f}s | "
            f"visual_before={total_visual:.2f}s | "
            f"scale={scale:.2f}"
        )

    return visual_blocks
