import os
from moviepy.editor import ImageClip, concatenate_videoclips
from moviepy.video.fx.resize import resize

from adapter.gradient_adapter_v3 import crear_gradiente_v3


def listar_imagenes_pool(base_path: str) -> list[str]:
    valid_ext = (".jpg", ".jpeg", ".png", ".webp")
    imgs = [
        os.path.join(base_path, f)
        for f in sorted(os.listdir(base_path))
        if f.lower().endswith(valid_ext)
    ]
    if not imgs:
        raise RuntimeError(f"No hay imágenes válidas en pool: {base_path}")
    return imgs


def crear_clip_imagen(
    ruta: str,
    duracion: float,
    motion_cfg: dict | None,
):
    clip = ImageClip(ruta).set_duration(duracion)

    if motion_cfg and motion_cfg.get("type") == "zoom":
        total = motion_cfg.get("total_percent", 2.0) / 100.0
        clip = clip.fx(
            resize,
            lambda t: 1 + (total * t / duracion)
        )

    return clip


def crear_fondo_pool_v3(
    *,
    duracion_total: float,
    base_path: str,
    image_duration_seconds: int,
    transition_cfg: dict | None = None,
    motion_cfg: dict | None = None,
):
    """
    Crea un fondo continuo usando un pool de imágenes.
    """

    imagenes = listar_imagenes_pool(base_path)

    clips = []
    tiempo_restante = duracion_total
    idx = 0

    while tiempo_restante > 0:
        ruta = imagenes[idx % len(imagenes)]
        dur = min(image_duration_seconds, tiempo_restante)

        clip = crear_clip_imagen(
            ruta=ruta,
            duracion=dur,
            motion_cfg=motion_cfg,
        )

        clips.append(clip)
        tiempo_restante -= dur
        idx += 1

    crossfade = 0
    if transition_cfg and transition_cfg.get("type") == "crossfade":
        crossfade = transition_cfg.get("seconds", 0)

    fondo = concatenate_videoclips(
        clips,
        method="compose",
        padding=-crossfade
    )

    grad = crear_gradiente_v3(duracion=fondo.duration)

    return fondo, grad
