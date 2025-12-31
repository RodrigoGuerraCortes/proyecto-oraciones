# generator/video/composer.py
import os
from moviepy.editor import CompositeVideoClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.fadein import fadein

from generator.image.cta import crear_bloque_cta

ANCHO = 1080
ALTO = 1920

WATERMARK_PATH = "marca_agua.png"


def componer_video(fondo, grad, titulo_clip, audio, clips_texto, salida: str):
    """
    Une:
      - fondo + grad + titulo + bloques
      - watermark
      - bloque final CTA (5s) con mismo fondo y grad
    Renderiza a salida.
    """
    
    #capas_principales = [fondo, grad, titulo_clip] + clips_texto
    capas_principales = [
        c for c in ([fondo, grad, titulo_clip] + clips_texto)
        if c is not None
    ]

    # watermark
    if os.path.exists(WATERMARK_PATH):
        try:
            wm = ImageClip(WATERMARK_PATH).resize(width=int(ANCHO * 0.22))
            wm = wm.set_duration(fondo.duration)
            wm = wm.set_opacity(0.85).fx(fadein, 0.7)

            pos_x = ANCHO - wm.w - 2
            pos_y = ALTO - wm.h - 2
            wm = wm.set_position((pos_x, pos_y))
            capas_principales.append(wm)
        except Exception:
            pass

    video_base = CompositeVideoClip(capas_principales).set_audio(audio)

    # CTA final
    DUR_FINAL = 5
    fondo_final = ImageClip("fondo_tmp.jpg").set_duration(DUR_FINAL).resize(lambda t: 1.04)
    grad_final = ImageClip("grad_tmp.png").set_duration(DUR_FINAL)

    capas_final = [fondo_final, grad_final]
    cta_clip = crear_bloque_cta(DUR_FINAL)
    if cta_clip:
        capas_final.append(cta_clip)

    video_cta = CompositeVideoClip(capas_final)

    final = concatenate_videoclips([video_base, video_cta])

    final.write_videofile(
        salida,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
    )
