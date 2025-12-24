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
    background_cfg = BackgroundConfig()
    title_style = TitleStyle()
    text_style = TextStyle()

    return {
        "render_cfg": render_cfg,
        "audio_req": audio_req,
        "background_cfg": background_cfg,
        "title_style": title_style,
        "text_style": text_style,
    }
