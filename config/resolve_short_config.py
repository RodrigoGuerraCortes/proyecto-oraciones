# config/config_resolver.py

import os
import sys


def _abs_path(base_storage_path: str, relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    return os.path.join(base_storage_path, relative_path)


def resolve_short_config(
    *,
    channel_config: dict,
    format_code: str,
    base_storage_path: str,
) -> dict:
    """
    Resuelve la configuración FINAL para un short (plain o stanzas).
    Devuelve SOLO datos planos (dicts), sin clases ni lógica de render.
    """

    if not base_storage_path:
        raise RuntimeError("base_storage_path is required")

    formats = channel_config.get("formats", {})
    if format_code not in formats:
        raise KeyError(f"Formato no encontrado: {format_code}")

    fmt = formats[format_code]

    # ------------------------------------------------------------------
    # CONTENT
    # ------------------------------------------------------------------
    content_cfg = fmt.get("content", {})
    global_content = channel_config.get("content", {})

    content_base_rel = global_content.get("base_path", "")
    content_path = content_cfg.get("path", "")

    content = {
        "type": content_cfg.get("type", "plain"),
        "base_path": os.path.join(
            base_storage_path,
            content_base_rel,
            content_path,
        ),
        "content_path": content_path,
        "max_lines": content_cfg.get("max_lines"),
        "max_blocks": content_cfg.get("max_blocks"),
        "seconds_per_block": content_cfg.get("seconds_per_block"),
    }

    # ------------------------------------------------------------------
    # VISUAL – BACKGROUND
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # VISUAL – TEXT & TITLE
    # ------------------------------------------------------------------
    layout = fmt.get("layout", {})
    title_layout = layout.get("title", {})
    text_layout = layout.get("text", {})
    watermark_layout = layout.get("watermark", {})

    title = {
        "font": title_layout.get("font", "DejaVuSerif-Bold.ttf"),
        "font_size": title_layout.get("font_size", 72),
        "line_spacing": title_layout.get("line_spacing", 14),
        "max_width_chars": title_layout.get("max_width_chars"),
        "y": title_layout.get("y", 120),
        "color": title_layout.get("color", "#FFFFFF"),
        "shadow": bool(title_layout.get("shadow", True)),
    }

    text = {
        "font": text_layout.get("font", "DejaVuSans.ttf"),
        "font_size": text_layout.get("font_size", 80),
        "line_spacing": text_layout.get("line_spacing", 24),
        "max_width": text_layout.get("max_width", 780),
        "y_start": text_layout.get("y_start", 440),
        "block_gap": text_layout.get("block_gap", 60),
        "outline_px": text_layout.get("outline_px", 0),
        "outline_color": text_layout.get("outline_color", "black"),
    }

    # ------------------------------------------------------------------
    # BRANDING
    # ------------------------------------------------------------------
    branding = channel_config.get("branding", {})

    watermark = {
        "path": _abs_path(base_storage_path, branding.get("water_mark")),
        "scale": watermark_layout.get("scale", 0.22),
        "margin": watermark_layout.get("margin", 12),
    }

    cta_cfg = fmt.get("cta", {})

    cta = {
        "enabled": bool(cta_cfg.get("enabled", False)),
        "seconds": int(cta_cfg.get("seconds", 0)),
        "path": _abs_path(base_storage_path, branding.get("cta")),
    }

    # ------------------------------------------------------------------
    # AUDIO
    # ------------------------------------------------------------------
    global_audio = channel_config.get("audio", {})
    music_cfg = global_audio.get("music", {})

    fmt_audio = fmt.get("audio", {})
    tts_cfg = fmt_audio.get("tts", {})

    music = {
        "enabled": bool(music_cfg.get("enabled", True) and fmt_audio.get("music", False)),
        "base_path": _abs_path(base_storage_path, music_cfg.get("base_path")),
        "strategy": music_cfg.get("strategy", "random"),
    }

    tts = {
        "enabled": bool(tts_cfg.get("enabled", False)),
        "engine": tts_cfg.get("engine"),
        "ratio": float(tts_cfg.get("ratio", 1.0)),
        "mode": tts_cfg.get("mode", "continuous"),
        "pause_after_title": float(tts_cfg.get("pause_after_title", 0.0)),
        "pause_between_blocks": float(tts_cfg.get("pause_between_blocks", 0.0)),
    }

    audio = {
        "music": music,
        "tts": tts,
    }


    # ------------------------------------------------------------------
    # RESULT FINAL
    # ------------------------------------------------------------------
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
            "title": title,
            "text": text,
            "watermark": watermark,
        },
        "audio": audio,
        "cta": cta,
    }
