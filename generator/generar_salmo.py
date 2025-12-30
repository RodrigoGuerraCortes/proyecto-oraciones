import os
import uuid
from moviepy.editor import (
    ImageClip,
    concatenate_audioclips,
    CompositeAudioClip
)
from moviepy.video.fx.fadein import fadein

from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.audio.tts_edge import generar_voz_edge
from generator.audio.silence import generar_silencio
from generator.video.composer import componer_video
from generator.content.fingerprinter import generar_fingerprint_contenido
from generator.cleanup import limpiar_temporales
from generator.utils.texto import normalizar_salmo_titulo
from generator.image.decision import decidir_imagen_video
from generator.experiments.voice_ab import decidir_tts_para_video
from db.repositories.video_repo import insert_video, fingerprint_existe_ultimos_dias

# -----------------------------
# Configuración Salmos
# -----------------------------
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 16        # SOLO modo clásico
CTA_DUR = 5
TTS_PORCENTAJE_SALMO = 0.50

PAUSA_ENTRE_ESTROFAS = 1.2
PAUSA_TITULO = 1.0


def generar_salmo(
    *,
    video_id,
    path_in: str,
    path_out: str,
    imagen_fija=None,
    musica_fija=None,
    modo_test=False
):
    # -------------------------------------------------
    # Texto base
    # -------------------------------------------------
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = normalizar_salmo_titulo(base)

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    # -------------------------------------------------
    # Decisión A/B TTS (50%)
    # -------------------------------------------------
    usar_tts = decidir_tts_para_video(
        porcentaje=TTS_PORCENTAJE_SALMO,
        seed=f"{texto}|{video_id}"
    )

    # -------------------------------------------------
    # Imagen / fondo
    # -------------------------------------------------
    imagen_usada = decidir_imagen_video(
        tipo="salmo",
        titulo=titulo,
        texto=texto
    )

    # =================================================
    # ========= MODO CLÁSICO (SIN VOZ) =================
    # =================================================
    if not usar_tts:

        if modo_test:
            duraciones = [2] * len(estrofas)
        else:
            duraciones = [SEGUNDOS_ESTROFA] * len(estrofas)

        dur_total = sum(duraciones)
        audio_duracion = dur_total + CTA_DUR

        fondo, grad = crear_fondo(dur_total, imagen_usada)

        crear_imagen_titulo(titulo, "titulo.png")
        titulo_clip = (
            ImageClip("titulo.png")
            .set_duration(dur_total)
            .set_position(("center", 120))
            .set_opacity(1)
        )

        clips = []
        t = 0

        for e, dur_e in zip(estrofas, duraciones):
            e = (
                e.replace("senor", "señor")
                 .replace("Senor", "Señor")
                 .replace("dios", "Dios")
            )

            crear_imagen_texto(e, "estrofa.png")
            c = (
                ImageClip("estrofa.png")
                .set_duration(dur_e)
                .set_position("center")
                .set_start(t)
                .fx(fadein, 0.8)
            )

            clips.append(c)
            t += dur_e

        audio, musica_usada = crear_audio(audio_duracion, musica_fija)

    # =================================================
    # ========= MODO TTS SINCRONIZADO ==================
    # =================================================
    else:
        voces = []
        duraciones = []

        # ---------- TÍTULO HABLADO ----------
        tts_titulo_path = f"tmp/tts_titulo_{uuid.uuid4().hex}.wav"
        voz_titulo = generar_voz_edge(
            texto=titulo,
            salida_wav=tts_titulo_path
        )

        voces.append(voz_titulo)
        voces.append(generar_silencio(PAUSA_TITULO))
        duraciones.append(voz_titulo.duration + PAUSA_TITULO)

        # ---------- ESTROFAS ----------
        for e in estrofas:
            tts_path = f"tmp/tts_{uuid.uuid4().hex}.wav"

            texto_tts = (
                e.replace("senor", "señor")
                 .replace("Senor", "Señor")
                 .replace("dios", "Dios")
            )

            voz = generar_voz_edge(
                texto=texto_tts,
                salida_wav=tts_path
            )

            voces.append(voz)
            voces.append(generar_silencio(PAUSA_ENTRE_ESTROFAS))
            duraciones.append(voz.duration + PAUSA_ENTRE_ESTROFAS)

        dur_total = sum(duraciones)
        audio_duracion = dur_total + CTA_DUR

        fondo, grad = crear_fondo(dur_total, imagen_usada)

        # ---------- TÍTULO VISUAL (solo mientras se dice) ----------
        crear_imagen_titulo(titulo, "titulo.png")
        titulo_clip = (
            ImageClip("titulo.png")
            .set_duration(duraciones[0])
            .set_position(("center", 120))
            .set_opacity(1)
        )

        # ---------- CLIPS DE TEXTO ----------
        clips = []
        t = duraciones[0]  # después del título hablado

        for e, dur_e in zip(estrofas, duraciones[1:]):
            crear_imagen_texto(e, "estrofa.png")

            c = (
                ImageClip("estrofa.png")
                .set_duration(dur_e)
                .set_position("center")
                .set_start(t)
                .fx(fadein, 0.8)
            )

            clips.append(c)
            t += dur_e

        voz_salmo = concatenate_audioclips(voces)

        if voz_salmo.duration < audio_duracion:
            voz_salmo = concatenate_audioclips([
                voz_salmo,
                generar_silencio(audio_duracion - voz_salmo.duration)
            ])
        else:
            voz_salmo = voz_salmo.subclip(0, audio_duracion)

        musica_clip, musica_usada = crear_audio(
            audio_duracion,
            musica_fija,
            usar_tts=False
        )

        musica_clip = musica_clip.volumex(0.35)
        voz_salmo = voz_salmo.volumex(1.0)

        audio = CompositeAudioClip([musica_clip, voz_salmo])

    # -------------------------------------------------
    # Fingerprint
    # -------------------------------------------------
    fingerprint = generar_fingerprint_contenido(
        tipo="salmo",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=audio_duracion
    )

    intentos = 0
    while fingerprint_existe_ultimos_dias(fingerprint) and intentos < 5:
        print("⚠ Contenido duplicado → cambiando música")

        musica_clip, musica_usada = crear_audio(
            audio_duracion,
            None,
            usar_tts=False
        )
        musica_clip = musica_clip.volumex(0.35)

        if usar_tts:
            audio = CompositeAudioClip([musica_clip, voz_salmo])
        else:
            audio = musica_clip

        fingerprint = generar_fingerprint_contenido(
            tipo="salmo",
            texto=texto,
            imagen=imagen_usada,
            musica=musica_usada,
            duracion=audio_duracion
        )

        intentos += 1

    licencia_path = (
        f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"
        if musica_usada
        else None
    )

    print("[DEBUG][DURATIONS]")
    print(f"  - dur_total: {dur_total}")
    print(f"  - CTA_DUR: {CTA_DUR}")
    print(f"  - fondo duration: {fondo.duration}")
    print(f"  - duracion total con CTA: {dur_total + CTA_DUR}")
    print(f"  - audio_duracion: {audio_duracion}")
    print(f"  - duraciones estrofas: {duraciones}")
    print(f"  - número estrofas: {len(estrofas)}")
    print(f"  - usar_tts: {usar_tts}")
    print(f"  - musica_usada: {musica_usada}")
    print(f"  - licencia_path: {licencia_path}")
    print(f"  - fingerprint: {fingerprint}")
    print("-------------------------------------------------")

    # -------------------------------------------------
    # Composición final
    # -------------------------------------------------
    componer_video(fondo, grad, titulo_clip, audio, clips, path_out)

    # -------------------------------------------------
    # Persistencia
    # -------------------------------------------------
    if os.path.exists(path_out):
        if not modo_test:
            insert_video({
                "id": video_id,
                "channel_id": 7,
                "archivo": path_out,
                "tipo": "salmo",
                "musica": musica_usada,
                "imagen": imagen_usada,
                "texto_base": texto,
                "fingerprint": fingerprint,
                "licencia": licencia_path,
                "metadata": {
                    "has_voice": usar_tts,
                    "voice_engine": "edge_tts" if usar_tts else None,
                    "voice_scope": "titulo+estrofa" if usar_tts else None,
                    "experiment": "tts_salmo_v2",
                    "tts_ratio": TTS_PORCENTAJE_SALMO,
                }
            })
    else:
        raise RuntimeError(f"No se pudo crear el archivo final: {path_out}")

    limpiar_temporales()
