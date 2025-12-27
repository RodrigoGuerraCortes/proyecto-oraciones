# generator/v2/pipeline/config_resolver.py

import os
from generator.v2.video.short_renderer import ShortRenderConfig
from generator.v2.video.background_renderer import BackgroundConfig
from generator.v2.video.title_renderer import TitleStyle
from generator.v2.video.text_renderer import TextStyle
from generator.v2.audio.models import AudioRequest
from dotenv import load_dotenv

load_dotenv()

BASE_STORAGE_PATH = os.getenv("BASE_STORAGE_PATH")


def resolve_short_config(
    *,
    channel_config: dict,
    format_code: str,
):
    if not BASE_STORAGE_PATH:
        raise RuntimeError("BASE_STORAGE_PATH is not defined")  

    fmt = channel_config["formats"][format_code]

    # -------------------------
    # Render config
    # -------------------------
    render_cfg = ShortRenderConfig(
        max_lines=fmt["content"].get("max_lines", 999),
        cta_seconds=fmt["cta"]["seconds"],
    )

    # -------------------------
    # Audio (v2 puro)
    # -------------------------
    audio_cfg = fmt["audio"]

    audio_req = AudioRequest(
        duration=0,                     # se setea luego
        tts_enabled=audio_cfg["tts"]["enabled"],
        tts_text=None,                  # se setea luego
        music_enabled=audio_cfg["music"],
    )

    # -------------------------
    # Estilos (default)
    # -------------------------


    visual = channel_config.get("visual", {})
    bg_cfg_raw = visual.get("background", {})

    blur_cfg = bg_cfg_raw.get("blur", {})

    blur_radius = (
        blur_cfg.get("radius", 6)
        if blur_cfg.get("enabled", True)
        else 0
    )

    background_cfg = BackgroundConfig(
        blur_radius=blur_radius,
        gradient_alpha=int(
            255 * bg_cfg_raw.get("gradient", {}).get("top_opacity", 0.4)
        ),
    )

    bg_base_rel = bg_cfg_raw.get("base_path", "assets/images")

    background_selector_cfg = {
        "base_path": os.path.join(BASE_STORAGE_PATH, bg_base_rel),
        "fallback": bg_cfg_raw.get("fallback", "default"),
        "ventana": bg_cfg_raw.get("window", 10),
    }

    # -------------------------
    # Paths varios
    # -------------------------

    content_cfg = channel_config.get("content", {})
    content_base_rel = content_cfg.get("base_path", "assets/texts")

    content_base_path = os.path.join(BASE_STORAGE_PATH, content_base_rel)


    branding = channel_config.get("branding", {})

    cta_path = branding.get("cta")
    watermark_path = branding.get("water_mark")

    if cta_path:
        cta_path = os.path.join(BASE_STORAGE_PATH, cta_path)

    if watermark_path:
        watermark_path = os.path.join(BASE_STORAGE_PATH, watermark_path)

    # -------------------------
    #Audio (v1 compatible)
    # -------------------------

    audio_root = channel_config.get("audio", {})
    music_root = audio_root.get("music", {})

    music_base_rel = music_root.get("base_path", "assets/music")
    music_enabled_global = bool(music_root.get("enabled", True))
    music_strategy = music_root.get("strategy", "random")

    music_base_path = os.path.join(BASE_STORAGE_PATH, music_base_rel)

    # Nota: music_enabled final = global AND formato
    music_enabled_final = music_enabled_global and bool(audio_cfg.get("music", False))

    audio_req = AudioRequest(
        duration=0,
        tts_enabled=audio_cfg["tts"]["enabled"],
        tts_text=None,
        music_enabled=music_enabled_final,
    )


    # -------------------------
    # Textos y Títulos
    # -------------------------

    layout = fmt.get("layout", {})
    text_layout = layout.get("text", {})
    title_layout = layout.get("title", {})

    text_style = TextStyle(
        font_path=f"/usr/share/fonts/truetype/dejavu/{text_layout.get('font', 'DejaVuSans.ttf')}",
        font_size=text_layout.get("font_size", 54),
        line_spacing=text_layout.get("line_spacing", 18),
        max_width_px=text_layout.get("max_width", 820),

        # outline
        outline_px=text_layout.get("outline_px", 2),
        outline_color=text_layout.get("outline_color", "black"),
    )

    title_style = TitleStyle(
        font_size=title_layout.get("font_size", 60),
        title_color=title_layout.get("color", "#E6C97A"),
        y=title_layout.get("y", 120),
    )

    return {
        "render_cfg": render_cfg,
        "audio_req": audio_req,
        "background_cfg": background_cfg,
        "background_selector_cfg": background_selector_cfg,
        "title_style": title_style,
        "text_style": text_style,
        "text_y_start": text_layout.get("y_start", 360),
        "cta_path": cta_path,
        "watermark_path": watermark_path,
        "content_base_path": content_base_path,
        "music_base_path": music_base_path,
        "music_strategy": music_strategy,
    }
