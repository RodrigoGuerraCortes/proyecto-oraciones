# generator/v2/video/short_renderer.py

from dataclasses import dataclass
from typing import List

from moviepy.editor import ImageClip

from generator.v2.content.parser import ParsedContent
from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import AudioRequest

from generator.v2.video.background_renderer import (
    render_background,
    BackgroundConfig,
)
from generator.v2.video.title_renderer import (
    render_title_image,
    TitleStyle,
)
from generator.v2.video.text_renderer import (
    render_text_block,
    TextStyle,
)
from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import (
    ComposerRequest,
    Overlay,
)

from generator.v2.cleanup.temp_files import cleanup_temp_files
from generator.v2.cleanup.models import TempFilesContext


# -------------------------------------------------
# Configuración mínima de render (viene de BD)
# -------------------------------------------------

@dataclass
class ShortRenderConfig:
    max_lines: int
    cta_seconds: int
    fade_seconds: float = 1.0
    title_y: int = 120


# -------------------------------------------------
# Renderer principal
# -------------------------------------------------

def render_short(
    *,
    parsed: ParsedContent,
    output_path: str,
    image_path: str,
    audio_req: AudioRequest,
    config: ShortRenderConfig,
    background_cfg: BackgroundConfig,
    title_style: TitleStyle,
    text_style: TextStyle,
    cta_image_path: str | None = None,
    modo_test: bool = False,
):
    """
    Renderiza un short COMPLETAMENTE genérico.
    No sabe si es oración, salmo u otro formato.
    """

    temp_files: List[str] = []

    # -------------------------------------------------
    # ⏱ Duraciones por bloque (policy ya resuelta)
    # -------------------------------------------------
    if modo_test:
        durations = [2.0] * len(parsed.blocks)
    else:
        durations = [
            _estimate_block_duration(
                block.text,
                config.max_lines
            )
            for block in parsed.blocks
        ]

    total_visual_duration = sum(durations)

    # -------------------------------------------------
    # 🎬 Fondo
    # -------------------------------------------------
    fondo, grad = render_background(
        image_path=image_path,
        duration=total_visual_duration,
        config=background_cfg,
    )

    temp_files.extend(["fondo_tmp.jpg", "grad_tmp.png"])

    # -------------------------------------------------
    # 🏷️ Título (imagen)
    # -------------------------------------------------
    title_img = "titulo_tmp.png"
    render_title_image(
        title=parsed.title,
        output_path=title_img,
        style=title_style,
    )
    temp_files.append(title_img)

    title_clip = (
        ImageClip(title_img)
        .set_duration(total_visual_duration)
        .set_position(("center", config.title_y))
        .set_opacity(1)
    )

    overlays: List[Overlay] = [
        Overlay(
            clip=title_clip,
            start=0,
            duration=total_visual_duration,
        )
    ]

    # -------------------------------------------------
    # 🧩 Bloques de texto
    # -------------------------------------------------
    t = 0.0

    for idx, (block, dur) in enumerate(zip(parsed.blocks, durations)):
        block_img = f"texto_{idx}.png"

        render_text_block(
            lines = block.text.splitlines(),
            output_path=block_img,
            style=text_style,
        )
        temp_files.append(block_img)

        clip = (
            ImageClip(block_img)
            .set_duration(dur)
            .set_position("center")
            .set_start(t)
        )

        overlays.append(
            Overlay(
                clip=clip,
                start=t,
                duration=dur,
            )
        )

        t += dur

    # -------------------------------------------------
    # 🔊 Audio
    # -------------------------------------------------
    audio_req.duration = total_visual_duration + config.cta_seconds
    audio_result = build_audio(audio_req)

    # -------------------------------------------------
    # 📣 CTA (opcional)
    # -------------------------------------------------
    cta_layers = None
    if cta_image_path:
        cta_clip = (
            ImageClip(cta_image_path)
            .set_duration(config.cta_seconds)
            .set_position("center")
        )
        cta_layers = [cta_clip]

    # -------------------------------------------------
    # 🎞️ Composición final
    # -------------------------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=[fondo, grad],
            overlays=overlays,
            audio=audio_result.audio_clip,
            cta_layers=cta_layers,
            output_path=output_path,
        )
    )

    # -------------------------------------------------
    # 🧹 Cleanup explícito (v2)
    # -------------------------------------------------
    cleanup_temp_files(
        TempFilesContext(files=temp_files)
    )

    return {
        "output": output_path,
        "music_used": audio_result.music_used,
        "has_voice": audio_req.tts_enabled,
    }


def _estimate_block_duration(text: str, max_lines: int) -> float:
    """
    Heurística simple v2:
    - ~2.5s por línea
    - mínimo 3s
    """
    lines = text.count("\n") + 1
    lines = min(lines, max_lines)
    return max(3.0, lines * 2.5)