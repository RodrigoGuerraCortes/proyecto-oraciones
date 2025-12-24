# generator/v2/pipeline/config_resolver.py

from generator.v2.video.short_renderer import ShortRenderConfig
from generator.v2.video.background_renderer import BackgroundConfig
from generator.v2.video.title_renderer import TitleStyle
from generator.v2.video.text_renderer import TextStyle
from generator.v2.audio.models import AudioRequest


def resolve_short_config(
    *,
    channel_config: dict,
    format_code: str,
):
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


    branding = channel_config.get("branding", {})
    bg_cfg_raw = branding.get("background", {})


    blur_radius = (
        bg_cfg_raw.get("radius", 6)
        if bg_cfg_raw.get("enabled", True)
        else 0
    )

    background_cfg = BackgroundConfig(
        blur_radius=blur_radius,
        gradient_alpha=int(
            255 * bg_cfg_raw.get("gradient", {}).get("top_opacity", 0.4)
        ),
    )

    background_selector_cfg = {
        "base_path": bg_cfg_raw.get("base_path", "imagenes"),
        "fallback": bg_cfg_raw.get("fallback", "default"),
        "ventana": bg_cfg_raw.get("window", 10),
    }

    layout = fmt.get("layout", {})
    text_layout = layout.get("text", {})
    title_layout = layout.get("title", {})

    text_style = TextStyle(
        font_path=f"/usr/share/fonts/truetype/dejavu/{text_layout.get('font', 'DejaVuSans.ttf')}",
        font_size=text_layout.get("font_size", 54),
        line_spacing=text_layout.get("line_spacing", 18),
        max_width_px=text_layout.get("max_width", 820),
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
    }
