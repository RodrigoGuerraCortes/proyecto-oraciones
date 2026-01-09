# config/resolve_tractor_config.py

import os

from config.resolve_long_config import _abs_path


def resolve_tractor_config(
    *,
    channel_config: dict,
    format_code: str,
    base_storage_path: str,
) -> dict:
    """
    Resolver de configuración para formatos tipo TRACTOR (long_tractor).

    Responsabilidades:
    - Resolver paths reales (texts, images, music)
    - Validar existencia de insumos
    - Devolver config lista para el engine
    """

    formats = channel_config.get("formats", {})
    fmt = formats[format_code]

    # -----------------------------
    # CONTENT
    # -----------------------------
    content_cfg = fmt.get("content", {})

    text_base_path = os.path.join(
        base_storage_path,
        content_cfg["base_path"]
    )

    blocks = content_cfg.get("blocks", [])
    repeatable_blocks = content_cfg.get("repeatable_blocks", [])

    if not blocks:
        raise RuntimeError("TRACTOR: no hay bloques definidos")

    for blk in blocks:
        blk_path = os.path.join(text_base_path, blk)
        if not os.path.isfile(blk_path):
            raise FileNotFoundError(f"Bloque no encontrado: {blk_path}")

    # -----------------------------
    # VISUAL
    # -----------------------------
    visual_cfg = fmt.get("visual", {})
    bg_cfg = visual_cfg.get("background", {})

    branding = channel_config.get("branding", {})
    layout = fmt.get("layout", {})
    watermark_layout = layout.get("watermark", {})

    watermark = {
        "path": _abs_path(base_storage_path, branding.get("water_mark")),
        "scale": watermark_layout.get("scale", 0.22),
        "margin": watermark_layout.get("margin", 12),
    }

    image_base_path = os.path.join(
        base_storage_path,
        bg_cfg["base_path"]
    )

    print("[Config Resolver] Tractor Image Pool Path:", image_base_path)

    if not os.path.isdir(image_base_path):
        raise FileNotFoundError(
            f"Pool de imágenes no encontrado: {image_base_path}"
        )

    # -----------------------------
    # AUDIO (MUSIC)
    # -----------------------------
    audio_cfg = fmt.get("audio", {})
    music_cfg = audio_cfg.get("music", {})

    music_path = None
    if music_cfg.get("enabled"):
        music_path = os.path.join(
            base_storage_path,
            music_cfg["base_path"],
            music_cfg["track"],
        )
        if not os.path.isfile(music_path):
            raise FileNotFoundError(f"Música no encontrada: {music_path}")

    # -----------------------------
    # RESULT FINAL
    # -----------------------------
    return {
        "engine": fmt["engine"],
        "identity": channel_config.get("identity", {}),
        "format": {
            "code": format_code,
            "display_name": fmt.get("display_name"),
            "type": fmt.get("format", "short"),
            "engine": fmt.get("engine"),
        },
        "target_duration_minutes": content_cfg.get("target_duration_minutes", 55),

        "content": {
            "base_path": text_base_path,
            "layers_path": _abs_path(base_storage_path, content_cfg.get("layers_path")),
            "blocks": blocks,
            "repeatable_blocks": repeatable_blocks,
        },

        "visual": {
            "base_path": image_base_path,
            "background_test": _abs_path(base_storage_path, visual_cfg.get("background_test")),
            "image_duration_seconds": bg_cfg.get("image_duration_seconds", 360),
            "transition": bg_cfg.get("transition", {}),
            "motion": bg_cfg.get("motion", {}),
            "watermark": watermark,
        },

        "audio": {
            "audio_layers_path": _abs_path(base_storage_path, audio_cfg.get("audio_layers_path")),
            "tts": audio_cfg.get("tts", {}),
            "music": {
                "enabled": music_cfg.get("enabled", False),
                "base_path": music_path,
                "loop": music_cfg.get("loop", {}),
                "volume": music_cfg.get("volume", -26),
            },
        },

        "cta": {
            "enabled": False
        }
    }
