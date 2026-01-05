# generator/v3/config/resolve_long_config.py
import os


def _abs_path(base_storage_path: str, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    return os.path.join(base_storage_path, relative_path)


def resolve_long_config(
    *,
    channel_config: dict,
    format_code: str,
    base_storage_path: str,
) -> dict:
    """
    Resolver LONG v3 (etapa simple).

    - NO define narrativa
    - NO define segments
    - NO define timeline
    - SOLO resuelve paths y flags
    """

    if not base_storage_path:
        raise RuntimeError("base_storage_path is required")

    formats = channel_config.get("formats", {})
    if format_code not in formats:
        raise KeyError(f"Formato no encontrado: {format_code}")

    fmt = formats[format_code]

    # --------------------------------------------------
    # CONTENT (paths simples)
    # --------------------------------------------------
    content_cfg = fmt.get("content", {})
    global_content = channel_config.get("content", {})

    content_base_rel = global_content.get("base_path", "")
    content_path = content_cfg.get("path", "")

    content = {
        # base común donde viven los textos del canal
        "base_path": os.path.join(base_storage_path, content_base_rel, content_path),
        "base_storage_path": os.path.join(base_storage_path, content_base_rel),
        # paths relativos
        "path": content_path,
        "script_guiado_path": content_cfg.get("script_guiado_path"),
        "script_guiado_name": content_cfg.get("script_guiado_name"),
    }

    if not content["path"]:
        raise ValueError("content.path es requerido para long")

    if not content["script_guiado_path"]:
        raise ValueError("content.script_guiado_path es requerido para long")

    if not content["script_guiado_name"]:
        raise ValueError("content.script_guiado_name es requerido para long")

    # --------------------------------------------------
    # VISUAL
    # --------------------------------------------------
    visual = channel_config.get("visual", {})
    bg_cfg = visual.get("background", {})

    blur_cfg = bg_cfg.get("blur", {})
    blur_enabled = blur_cfg.get("enabled", True)

    background = {
        "base_path": _abs_path(base_storage_path, bg_cfg.get("base_path")),
        "fallback": bg_cfg.get("fallback", "default"),
        "blur_radius": blur_cfg.get("radius", 4) if blur_enabled else 0,
        "gradient": {
            "enabled": bg_cfg.get("gradient", {}).get("enabled", True),
            "top_opacity": bg_cfg.get("gradient", {}).get("top_opacity", 0.85),
            "bottom_opacity": bg_cfg.get("gradient", {}).get("bottom_opacity", 0.9),
        },
    }

    layout = fmt.get("layout", {})
    text_layout = layout.get("text", {})

    text = {
        "font": text_layout.get("font", "DejaVuSans.ttf"),
        "font_size": text_layout.get("font_size", 80),
        "line_spacing": text_layout.get("line_spacing", 24),
        "max_width": text_layout.get("max_width", 780),
        "y_start": text_layout.get("y_start", 440),
        "outline_px": text_layout.get("outline_px", 0),
        "outline_color": text_layout.get("outline_color", "black"),
    }

    branding = channel_config.get("branding", {})
    watermark = {
        "path": _abs_path(base_storage_path, branding.get("water_mark")),
        "scale": layout.get("watermark", {}).get("scale", 0.22),
        "margin": layout.get("watermark", {}).get("margin", 12),
    }

    # --------------------------------------------------
    # AUDIO
    # --------------------------------------------------
    global_audio = channel_config.get("audio", {})
    music_cfg = global_audio.get("music", {})

    fmt_audio = fmt.get("audio", {})
    tts_cfg = fmt_audio.get("tts", {})

    audio = {
        "music": {
            "enabled": bool(fmt_audio.get("music", True)),
            "base_path": _abs_path(base_storage_path, music_cfg.get("base_path")),
            "strategy": music_cfg.get("strategy", "random"),
        },
        "tts": {
            "enabled": bool(tts_cfg.get("enabled", False)),
            "engine": tts_cfg.get("engine"),
        },
    }

    # --------------------------------------------------
    # CTA
    # --------------------------------------------------
    cta_cfg = fmt.get("cta", {})

    cta = {
        "enabled": bool(cta_cfg.get("enabled", False)),
        "seconds": int(cta_cfg.get("seconds", 5)),
    }

    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------
    return {
        "identity": channel_config.get("identity", {}),
        "format": {
            "code": format_code,
            "display_name": fmt.get("display_name"),
            "type": fmt.get("format", "long"),
            "engine": fmt.get("engine"),
        },
        "content": content,
        "visual": {
            "background": background,
            "text": text,
            "watermark": watermark,
        },
        "audio": audio,
        "cta": cta,
    }
