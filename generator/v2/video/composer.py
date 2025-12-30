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
    MODELO:
    - Un solo timeline (texto + CTA)
    - CTA es OVERLAY visual (no segmento concatenado)
    - El audio ya viene con la duración correcta
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
    print(f"[COMPOSE-DBG] base_video.duration={base_video.duration:.2f}s")

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
    print(f"[COMPOSE-DBG] main_video.duration={main_video.duration:.2f}s")

    # ---------------------------------
    # CTA como OVERLAY (NO concatenar)
    # ---------------------------------
    cta_overlays = []
    if request.cta_layers:
        cta_duration = request.cta_layers[0].duration
        cta_start = max(0.0, main_video.duration - cta_duration)

        print(
            "[COMPOSE-DBG] "
            f"CTA overlay | start={cta_start:.2f}s | "
            f"duration={cta_duration:.2f}s"
        )

        for cta in request.cta_layers:
            cta_overlays.append(
                cta
                .set_start(cta_start)
                .set_duration(cta_duration)
            )

    # ---------------------------------
    # Composición FINAL (sin concatenar)
    # ---------------------------------
    final = gateway.composite([main_video] + cta_overlays)
    print(f"[COMPOSE-DBG] final.duration(before_audio)={final.duration:.2f}s")

    # ---------------------------------
    # Audio (SIN forzar duración)
    # ---------------------------------
    if request.audio is not None:
        final = final.set_audio(request.audio)

        print(
            "[COMPOSE-DBG] "
            f"audio attached | "
            f"audio.duration={request.audio.duration:.2f}s | "
            f"video.duration={final.duration:.2f}s"
        )

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
