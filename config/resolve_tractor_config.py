# config/resolve_tractor_config.py

import os
import sys
import json
from config.resolve_long_config import _abs_path


def resolve_tractor_config(
    *,
    channel_config: dict,
    format_code: str,
    base_storage_path: str,
    tractor: str | None = None,
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
    channel_code = channel_config.get("identity", {}).get("code")

    print("[Config Resolver] Resolviendo configuración TRACTOR para formato:", format_code)
    print("[Config Resolver] Base Storage Path:", base_storage_path)
    print("[Config Resolver] Formato Config:", fmt)
    print("[Config Resolver] Código recibido:", channel_config.get("identity", {}).get("code"))


    # -----------------------------
    # DEFINICION DE PATHS
    # -----------------------------
    text_base_path = os.path.join(
        base_storage_path,
        'assets/texts/',
        channel_code,
        'tractores/',
        tractor
    )

    image_base_path = os.path.join(
        base_storage_path,
        'assets/images/',
        channel_code,
        'tractores/',
        tractor
    )


    music_path = None
    audio_cfg = fmt.get("audio", {})
    music_cfg = audio_cfg.get("music", {})
    music_path = traer_path_music(music_cfg, base_storage_path, channel_code, tractor)
   
    layers_path = os.path.join(
        base_storage_path,
        'generated',
        channel_code,
        'longs/tractores/',
        tractor,
        'layers'
    )

    audio_layers_path = os.path.join(
        base_storage_path,
        'generated',
        channel_code,
        'longs/tractores/',
        tractor,
        'audio'
    )

    sequence_path = os.path.join(
        base_storage_path,
        'generated',
        channel_code,
        'longs/tractores/',
        tractor,
        'sequence'
    )


    print("[Config Resolver] Tractor Text Base Path:", text_base_path)
    print("[Config Resolver] Tractor Image Base Path:", image_base_path)
    print("[Config Resolver] Tractor Music Base Path:", music_path)
    print("[Config Resolver] Tractor Layers Path:", layers_path)
    print("[Config Resolver] Tractor Audio Layers Path:", audio_layers_path)
    print("[Config Resolver] Tractor Sequence Path:", sequence_path)

    #sys.exit(0)

    # -----------------------------
    # CONTENT, BLOCKS AND REPEATABLE BLOCKS
    # -----------------------------
    content_cfg = fmt.get("content", {})

    descriptor_path = os.path.join(text_base_path, "tractor.json")

    if not os.path.isfile(descriptor_path):
        raise FileNotFoundError(
            f"TRACTOR: descriptor no encontrado: {descriptor_path}"
        )

    with open(descriptor_path, "r", encoding="utf-8") as f:
        tractor_desc = json.load(f)


    blocks = tractor_desc.get("blocks", [])
    repeatable_blocks = tractor_desc.get("repeatable_blocks", [])
    silence_rules = tractor_desc.get("silence_rules", {})
    tts_prompt = tractor_desc.get("tts_prompt", {})

    print("[TractorDesc]", silence_rules)



    target_duration_minutes = tractor_desc.get("target_duration_minutes")
    source = tractor_desc.get("source", "filesystem")

    if not blocks:
        raise RuntimeError("TRACTOR: 'blocks' vacío o no definido en tractor.json")

    if not isinstance(blocks, list):
        raise TypeError("TRACTOR: 'blocks' debe ser una lista")

    if not isinstance(repeatable_blocks, list):
        raise TypeError("TRACTOR: 'repeatable_blocks' debe ser una lista")

    if not isinstance(target_duration_minutes, (int, float)):
        raise TypeError("TRACTOR: 'target_duration_minutes' inválido")

    if source != "filesystem":
        raise ValueError(f"TRACTOR: source no soportado: {source}")


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

    # Validate image base path
    if not os.path.isdir(image_base_path):
        raise FileNotFoundError(
            f"Pool de imágenes no encontrado: {image_base_path}"
        )

 

   

    # -----------------------------
    # RESULT FINAL
    # -----------------------------
    return {
        "engine": fmt["engine"],
        "identity": channel_config.get("identity", {}),
        "sequence_path": sequence_path,
        "format": {
            "code": format_code,
            "display_name": fmt.get("display_name"),
            "type": fmt.get("format", "short"),
            "engine": fmt.get("engine"),
        },
        "target_duration_minutes": content_cfg.get("target_duration_minutes", 55),

        "content": {
            "base_path": text_base_path,
            "layers_path": layers_path,
            "blocks": blocks,
            "repeatable_blocks": repeatable_blocks,
            "silence_rules": silence_rules,
            "tts_prompt": tts_prompt,
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
            "audio_layers_path": audio_layers_path,
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


def traer_path_music(music_cfg, base_storage_path, channel_code, tractor): 

    if music_cfg.get("enabled"):
        music_dir = os.path.join(
            base_storage_path,
            "assets",
            "music",
            channel_code,
            "tractores",
            tractor
        )

    if not os.path.isdir(music_dir):
        raise FileNotFoundError(
            f"Directorio de música no encontrado: {music_dir}"
        )

    mp3_files = [
        f for f in os.listdir(music_dir)
        if f.lower().endswith(".mp3")
    ]

    if len(mp3_files) == 0:
        raise FileNotFoundError(
            f"No se encontró ningún mp3 en: {music_dir}"
        )

    if len(mp3_files) > 1:
        raise ValueError(
            f"Se encontró más de un mp3 en {music_dir}: {mp3_files}"
        )

    music_file = os.path.join(music_dir, mp3_files[0])

    return music_file


