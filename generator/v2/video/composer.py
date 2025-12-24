# generator/v2/video/composer.py

from generator.v2.video.moviepy_gateway import MoviePyGatewayImpl
from generator.v2.video.composer_models import (
    ComposerRequest,
    ComposerResult,
    Overlay,
)


def compose_video(
    *,
    request: ComposerRequest,
    gateway=None,
) -> ComposerResult:
    """
    Compone el video final usando únicamente datos ya decididos.
    """

    gateway = gateway or MoviePyGatewayImpl()

    # Base (fondo + gradiente)
    base_video = gateway.composite(request.base_layers)

    # Overlays (título, texto, watermark, etc.)
    overlay_clips = []
    for o in request.overlays:
        clip = (
            o.clip
            .set_start(o.start)
            .set_duration(o.duration)
            .set_position(o.position)
            .set_opacity(o.opacity)
        )
        overlay_clips.append(clip)

    main_video = (
        gateway
        .composite([base_video] + overlay_clips)
        .set_audio(request.audio)
    )

    # CTA opcional
    if request.cta_layers:
        cta_video = gateway.composite(request.cta_layers)
        final = gateway.concat([main_video, cta_video])
    else:
        final = main_video

    gateway.write(final, request.output_path, request.fps)

    return ComposerResult(
        output_path=request.output_path,
        duration=final.duration,
    )
