# generator/video/render.py
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein


def clip_titulo(path_png: str, duracion: float):
    return (
        ImageClip(path_png)
        .set_duration(duracion)
        .set_position(("center", 120))
        .set_opacity(1)
    )


def clips_texto_bloques(bloques: list[str], duraciones: list[float], imagen_tmp: str, modo_fade: bool):
    """
    Crea lista de ImageClips con start acumulado si corresponde.
    """
    clips = []
    t = 0.0
    for texto, dur in zip(bloques, duraciones):
        c = ImageClip(imagen_tmp).set_duration(dur).set_position("center")
        if modo_fade and len(bloques) > 1:
            c = c.fx(fadein, 1).set_start(t)
        clips.append(c)
        t += dur
    return clips
