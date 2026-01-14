# long/generar_long_oracion_generico.py


import os
import uuid
import json
import sys

from pathlib import Path


from moviepy.editor import ImageClip, CompositeAudioClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.volumex import volumex

from adapter.fondo_adapter import crear_fondo_v3
from adapter.titulo_adapter import crear_imagen_titulo_v3
from adapter.texto_adapter import crear_imagen_texto_v3
from adapter.composer_adapter import componer_video_v3

from adapter.audio_fingerprint_adapter import resolver_audio_y_fingerprint_v3
from adapter.persistir_adapter import persistir_video_v3

from generator.audio.tts_edge import generar_voz_edge, _normalizar_texto_tts, suavizar_finales_tts
from adapter.audio_adapter import crear_audio_v3 
from generator.audio.silence import generar_silencio 
from normalizacion.es import normalize_spanish

from generator.decision import decidir_imagen_video 
from generator.cleanup import limpiar_temporales


# --------------------------------------------------
# Defaults (copiados de v1 y simplificados)
# --------------------------------------------------
CTA_DUR_DEFAULT = 5

FADE_IN = 0.5
FADE_OUT = 0.5

SILENCIO_CORTO = 3.0
SILENCIO_MEDITATIVO = 6.0
SILENCIO_REFLEXION = 60.0
SILENCIO_REFLEXION_TEST = 6.0


# --------------------------------------------------
# Helpers locales
# --------------------------------------------------
def _split_parrafos(texto: str) -> list[str]:
    return [p.strip() for p in texto.split("\n\n") if p.strip()]


def _duracion_silencio_frase(frase: str) -> float:
    f = frase.lower()
    if "silencio" in f or "permanece" in f:
        return SILENCIO_MEDITATIVO
    return SILENCIO_CORTO


def _leer_archivo_texto(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
    
def _elegir_archivo_script(script_dir: str) -> tuple[str, str]:
    """
    Devuelve (path, nombre_sin_ext) de un script guiado.
    Hoy: elección simple (ordenada / random).
    Mañana: se puede conectar a DB sin tocar el generador.
    """
    archivos = [
        f for f in os.listdir(script_dir)
        if f.endswith(".txt")
    ]

    if not archivos:
        raise RuntimeError(f"No hay scripts guiados en {script_dir}")

    archivos.sort()  # orden estable (LONG_A, LONG_B, ...)
    elegido = archivos[0]  # por ahora el primero

    path = os.path.join(script_dir, elegido)
    return path, elegido.replace(".txt", "")



# --------------------------------------------------
# Generador principal
# --------------------------------------------------
def generar_long_guiado_generico(
    *,
    resolved_config: dict,
    text_path: str,
    output_path: str,
    video_id: str,
    channel_id: int,
    modo_test: bool = False,
    force_tts: bool | None = None,
    music_path: str,
):
    """
    v3 LONG – enfoque simple (estilo short)

    - Timeline único
    - Música continua
    - TTS por clips (título, intro, guion)
    - Silencios explícitos
    """

    # --------------------------------------------------
    # 1) Paths base desde config
    # --------------------------------------------------
    content_cfg = resolved_config["content"]
    base_path = content_cfg["base_path"]
    bg_cfg = resolved_config["visual"]["background"]
    base_path_assest = bg_cfg.get("base_path")
    

    # --------------------------------------------------
    # 2) Leer texto base
    # --------------------------------------------------

    print("[GENERAR LONG]Leyendo texto base en:", text_path)
   
    texto = _leer_archivo_texto(text_path)

    print("[GENERAR LONG]Texto leído:", len(texto), "caracteres")

    if not texto:
        raise ValueError("Texto vacío")

    base = os.path.splitext(os.path.basename(text_path))[0]
    titulo = base.replace("_", " ").title()
    
    parrafos = _split_parrafos(texto)
    if not parrafos:
        raise ValueError("Texto base no tiene párrafos")

    texto_intro = parrafos[0]

    # --------------------------------------------------
    # 3) Leer guion guiado
    # --------------------------------------------------
    script_dir = os.path.join(
    content_cfg["base_storage_path"],
    content_cfg["script_guiado_path"],
    )

    print("[GENERAR LONG]Leyendo guion guiado en:", script_dir)

    script_path, guion_guiado_id = _elegir_archivo_script(script_dir)

    texto_guion = _leer_archivo_texto(script_path)

    if not texto_guion:
        raise ValueError("Guion guiado vacío")

    frases_guiadas = [
        l.strip().strip('",')
        for l in texto_guion.splitlines()
        if l.strip()
    ]

    if not frases_guiadas:
        raise ValueError("Guion guiado no contiene frases válidas")

    # --------------------------------------------------
    # 4) Decidir imagen
    # --------------------------------------------------
    format_code = resolved_config["format"]["code"]

    texto_para_imagen = texto + "\n" + "\n".join(frases_guiadas[:10])
    imagen_usada = decidir_imagen_video(
        tipo=format_code,
        titulo=titulo,
        texto=texto_para_imagen,
        base_path_assest=base_path_assest,
    )

    # --------------------------------------------------
    # 5) Flags audio / TTS / CTA
    # --------------------------------------------------
    audio_cfg = resolved_config["audio"]
    tts_cfg = audio_cfg.get("tts", {})
    music_cfg = audio_cfg.get("music", {})

    usar_tts = bool(tts_cfg.get("enabled", True))
    if force_tts is not None:
        usar_tts = force_tts

    cta_cfg = resolved_config.get("cta", {})
    cta_seconds = int(cta_cfg.get("seconds", CTA_DUR_DEFAULT)) if cta_cfg.get("enabled") else 0

    # --------------------------------------------------
    # 6) Timeline de voz
    # --------------------------------------------------
    voz_clips = []
    texto_clips = []

    t = 0.0

    # --- Título ---
    crear_imagen_titulo_v3(titulo=titulo, output=base_path_assest + "/tmp/titulo.png")

    if usar_tts:
        wav = f"tmp/tts_titulo_{uuid.uuid4().hex}.wav"
        voz = generar_voz_edge(
            texto=suavizar_finales_tts(_normalizar_texto_tts(titulo)),
            salida_wav=wav,
        ).set_start(t)

        voz_clips.append(voz)

        titulo_clip = (
            ImageClip(base_path_assest + "/tmp/titulo.png")
            .set_start(t)
            .set_duration(voz.duration)
            .set_position("center")
            .fx(fadein, 0.8)
            .fx(fadeout, 0.8)
        )

        t += float(voz.duration) + 1.0
    else:
        titulo_clip = (
            ImageClip(base_path_assest + "/tmp/titulo.png")
            .set_start(t)
            .set_duration(3.0 if modo_test else 6.0)
            .set_position("center")
            .fx(fadein, 0.8)
            .fx(fadeout, 0.8)
        )
        t += titulo_clip.duration + 1.0

    # --- Intro ---
    if usar_tts:
        wav = f"tmp/tts_intro_{uuid.uuid4().hex}.wav"
        voz = generar_voz_edge(
            texto=suavizar_finales_tts(_normalizar_texto_tts(texto_intro)),
            salida_wav=wav,
        ).set_start(t)

        voz_clips.append(voz)

        # ✅ VISUAL DEL INTRO
        crear_imagen_texto_v3(texto=texto_intro, output=base_path_assest + "/tmp/intro_txt.png")
        intro_clip = (
            ImageClip(base_path_assest + "/tmp/intro_txt.png")
            .set_start(t)
            .set_duration(voz.duration)
            .set_position("center")
            .fx(fadein, FADE_IN)
            .fx(fadeout, FADE_OUT)
        )
        texto_clips.append(intro_clip)

        t += float(voz.duration) + 2.0


    # --- Guion guiado ---
    frase_final = "Ahora, te invito a permanecer un minuto en silencio y reflexión."

    if modo_test:
        frases_guiadas = frases_guiadas[:4]

    frases_guiadas = list(frases_guiadas)  # defensivo
    frases_guiadas.append(frase_final)

    for idx, frase in enumerate(frases_guiadas, start=1):
        if usar_tts:
            wav = f"tmp/tts_guiada_{uuid.uuid4().hex}.wav"
            voz = generar_voz_edge(
                texto=suavizar_finales_tts(_normalizar_texto_tts(frase)),
                salida_wav=wav,
            ).set_start(t)

            voz_clips.append(voz)

            crear_imagen_texto_v3(texto=frase, output=f"guiada_txt_{idx}.png")
            txt_clip = (
                ImageClip(f"guiada_txt_{idx}.png")
                .set_start(t)
                .set_duration(voz.duration)
                .set_position("center")
                .fx(fadein, FADE_IN)
                .fx(fadeout, FADE_OUT)
            )
            texto_clips.append(txt_clip)

            t += float(voz.duration)

        t += 0.6 if modo_test else _duracion_silencio_frase(frase)

    t += SILENCIO_REFLEXION_TEST if modo_test else SILENCIO_REFLEXION

    # --------------------------------------------------
    # 7) Duraciones finales
    # --------------------------------------------------
    if modo_test:
        dur_total = t
    else:
        dur_total = max(t, 180.0)
    audio_duracion = dur_total + cta_seconds

    # --------------------------------------------------
    # 8) Fondo
    # --------------------------------------------------
    fondo, grad = crear_fondo_v3(
        duracion=dur_total,
        ruta_imagen=imagen_usada,
        base_path=bg_cfg.get("base_path"),
    )

    # --------------------------------------------------
    # 9) Música + mezcla
    # --------------------------------------------------
    if music_cfg.get("enabled", True):
        musica_clip, musica_usada = crear_audio_v3(
            duracion=audio_duracion,
            usar_tts=False,
            texto_tts=None,
            music_path=music_cfg.get("base_path"),
        )
        musica_clip = volumex(musica_clip, 0.18)
    else:
        musica_clip = None
        musica_usada = None

    if usar_tts and voz_clips:
        voz_mix = CompositeAudioClip(voz_clips).set_duration(audio_duracion)
    else:
        voz_mix = generar_silencio(audio_duracion)

    audio_final = (
        CompositeAudioClip([musica_clip, voz_mix]).set_duration(audio_duracion)
        if musica_clip
        else voz_mix
    )

    # --------------------------------------------------
    # 10) Fingerprint
    # --------------------------------------------------
    audio, musica_usada, fingerprint = resolver_audio_y_fingerprint_v3(
        tipo=format_code,
        texto=texto_para_imagen,
        imagen_usada=imagen_usada,
        audio_duracion=int(round(audio_duracion)),
        usar_tts=usar_tts,
        audio_inicial=(audio_final, musica_usada),
    )

    # --------------------------------------------------
    # 11) Composición final
    # --------------------------------------------------
    componer_video_v3(
        fondo=fondo,
        grad=grad,
        titulo_clip=titulo_clip,
        audio=audio,
        text_clips=texto_clips,
        output_path=output_path,
        visual_cfg=resolved_config["visual"],
        cta_cfg=cta_cfg,
        base_path_assest=base_path_assest,
    )

    if not os.path.exists(output_path):
        raise RuntimeError(f"No se pudo generar el video: {output_path}")

    # --------------------------------------------------
    # 12) Persistencia
    # --------------------------------------------------
    licencia_path = ( 
        audio_cfg['music']['base_path'] + "/licence/licence_" + musica_usada.replace('.mp3','') + ".txt"
        if musica_usada
        else None
    )

    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo=format_code,
        output_path=output_path,
        texto=texto_para_imagen,
        imagen_usada=imagen_usada,
        musica_usada=musica_usada,
        fingerprint=fingerprint,
        usar_tts=usar_tts,
        modo_test=modo_test,
        licencia_path=licencia_path,
        metadata_extra={
            "guion_guiado_id": guion_guiado_id,
        },
    )

    limpiar_temporales(base_path_assest)
