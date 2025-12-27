# generator/v2/video/composer.py

from generator.v2.video.moviepy_gateway import MoviePyGatewayImpl
from generator.v2.video.composer_models import (
    ComposerRequest,
    ComposerResult,
)


def compose_video(
    *,
    request: ComposerRequest,
    gateway=None,
) -> ComposerResult:
    """
    Compone el video final usando únicamente datos ya decididos.
    """

    print(
        "[COMPOSE] "
        f"base_layers={len(request.base_layers)} | "
        f"cta_layers={len(request.cta_layers) if request.cta_layers else 0} | "
        f"audio={'yes' if request.audio else 'no'}"
    )

    gateway = gateway or MoviePyGatewayImpl()

    # ---------------------------------
    # Base (fondo + gradiente)
    # ---------------------------------
    base_video = gateway.composite(request.base_layers)

    # ---------------------------------
    # Overlays (título, texto, watermark, etc.)
    # ---------------------------------
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

    main_video = gateway.composite([base_video] + overlay_clips)

    # ---------------------------------
    # CTA opcional
    # ---------------------------------
    if request.cta_layers:
        cta_video = gateway.composite(request.cta_layers).set_audio(None)
        final = gateway.concat([main_video, cta_video])
    else:
        cta_video = None
        final = main_video

    # ---------------------------------
    # DEBUG: duraciones reales ANTES de set_audio
    # ---------------------------------
    if request.audio is not None:
        print(
            "[AUDIO-DEBUG] "
            f"audio.duration={request.audio.duration:.2f}s | "
            f"main_video.duration={main_video.duration:.2f}s | "
            f"final.duration={final.duration:.2f}s | "
            f"has_cta={bool(cta_video)}"
        )

    print(
        "[AUDIO-DEBUG] "
        f"audio_assigned_to=final | has_cta={bool(cta_video)}"
    )

    # ---------------------------------
    # FIX TEMPORAL: forzar duración del audio
    # ---------------------------------
    if request.audio is not None:
        forced_audio = request.audio.set_duration(final.duration)

        print(
            "[AUDIO-DEBUG] "
            f"forced_audio.duration={forced_audio.duration:.2f}s | "
            f"final.duration={final.duration:.2f}s"
        )

        final = final.set_audio(forced_audio)

    # ---------------------------------
    # Render
    # ---------------------------------
    gateway.write(final, request.output_path, request.fps)

    print(
        f"[COMPOSE] done | output={request.output_path} | "
        f"duration={final.duration:.2f}s"
    )

    return ComposerResult(
        output_path=request.output_path,
        duration=final.duration,
    )
