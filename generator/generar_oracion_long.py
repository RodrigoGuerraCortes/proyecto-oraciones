import os

from moviepy.editor import ImageClip, CompositeAudioClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.audio.fx.volumex import volumex

from generator.audio.tts_edge import generar_voz_edge, _normalizar_texto_tts
from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.video.composer import componer_video
from generator.content.fingerprinter import generar_fingerprint_contenido
from generator.cleanup import limpiar_temporales
from generator.image.decision import decidir_imagen_video
from db.repositories.video_repo import insert_video

from generator.audio.silence import generar_silencio
from generator.utils.texto import normalizar_titulo_es
from generator.content.selector import elegir_siguiente_guion_long, elegir_texto_para

# -----------------------
# CONFIGURACIÓN GENERAL
# -----------------------

CTA_DUR = 5

DUR_OBJ_MIN = 180
DUR_OBJ_MAX = 300

TEXTO_ONSCREEN_MIN = 8
TEXTO_ONSCREEN_MAX = 14

FADE_TEXTO_IN = 0.6
FADE_TEXTO_OUT = 0.6

SILENCIO_CORTO = 3.0
SILENCIO_MEDITATIVO = 6.0
SILENCIO_FINAL = 6.0

VOZ_DIR = "voz"
DUR_TEST_LONG = 28

# -----------------------
# UTILIDADES
# -----------------------

def _split_parrafos(texto: str) -> list[str]:
    return [p.strip() for p in texto.split("\n\n") if p.strip()]


def _word_count(s: str) -> int:
    return len([w for w in s.split() if w.strip()])


def _asignar_duraciones(parrafos: list[str], dur_total: int) -> list[float]:
    counts = [_word_count(p) for p in parrafos]
    total = sum(counts) or 1
    piso = 18.0

    durs = [max(piso, dur_total * (c / total)) for c in counts]
    factor = dur_total / sum(durs)
    durs = [d * factor for d in durs]
    durs[-1] += dur_total - sum(durs)

    return durs


def _duracion_silencio_frase(frase: str) -> float:
    """
    Silencio contextual según el contenido espiritual de la frase
    """
    f = frase.lower()
    if "silencio" in f or "permanece" in f:
        return SILENCIO_MEDITATIVO
    return SILENCIO_CORTO


# -----------------------
# FUNCIÓN PRINCIPAL
# -----------------------

def generar_oracion_long(
    *,
    video_id,
    path_in: str | None,
    path_out: str,
    musica_fija: str | None = None,
    duracion_objetivo: int = 240,
    modo_test: bool = False
):
    # -----------------------
    # TEXTO BASE
    # -----------------------

    # -----------------------
    # TEXTO BASE (NO REPETIBLE EN LONG)
    # -----------------------

    if path_in is None:
        path_in, _ = elegir_texto_para("long")

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        raise RuntimeError("Texto vacío")

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = normalizar_titulo_es(base.replace("_", " ").title())

    dur_total = DUR_TEST_LONG if modo_test else max(
        DUR_OBJ_MIN, min(DUR_OBJ_MAX, duracion_objetivo)
    )

    parrafos = _split_parrafos(texto)
    texto_intro = parrafos[0]
    duraciones = _asignar_duraciones(parrafos, dur_total)

    # -----------------------
    # FONDO
    # -----------------------

    imagen_usada = decidir_imagen_video("long", titulo, texto)
    fondo, grad = crear_fondo(dur_total, imagen_usada)

    os.makedirs(VOZ_DIR, exist_ok=True)

    # -----------------------
    # VOZ + TÍTULO
    # -----------------------

    voz_titulo_path = os.path.join(VOZ_DIR, f"titulo_{video_id}.wav")
    voz_titulo = generar_voz_edge(
        texto=_normalizar_texto_tts(titulo),
        salida_wav=voz_titulo_path
    ).set_start(0)

    dur_voz_titulo = voz_titulo.duration

    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = (
        ImageClip("titulo.png")
        .set_duration(dur_voz_titulo)
        .set_position(("center", "center"))
        .fx(fadein, 0.8)
        .fx(fadeout, 0.8)
    )

    # -----------------------
    # VOZ ORACIÓN BASE
    # -----------------------

    voz_intro_path = os.path.join(VOZ_DIR, f"intro_{video_id}.wav")
    voz_intro = generar_voz_edge(
        texto=_normalizar_texto_tts(texto_intro),
        salida_wav=voz_intro_path
    ).set_start(dur_voz_titulo + 1.0)

    dur_voz_intro = voz_intro.duration

    # -----------------------
    # VOZ GUIADA (CON SILENCIO INTELIGENTE)
    # -----------------------

    clips_guiados = []
    clips_texto_guiado = []

    t_actual = dur_voz_titulo + dur_voz_intro + 3.0

    guion_id, guion_guiado = elegir_siguiente_guion_long(channel_id=7)

    print(f"[LONG] video_id={video_id} guion={guion_id}")


    for idx, frase in enumerate(guion_guiado, start=1):
        voz_path = os.path.join(VOZ_DIR, f"guiada_{video_id}_{idx}.wav")

        voz_clip = generar_voz_edge(
            texto=_normalizar_texto_tts(frase),
            salida_wav=voz_path
        ).set_start(t_actual)

        clips_guiados.append(voz_clip)

        # TEXTO GUIADO EN PANTALLA
        crear_imagen_texto(frase, f"guiada_txt_{idx}.png")

        texto_clip = (
            ImageClip(f"guiada_txt_{idx}.png")
            .set_start(t_actual)
            .set_duration(voz_clip.duration)
            .set_position("center")
            .fx(fadein, 0.5)
            .fx(fadeout, 0.5)
        )

        clips_texto_guiado.append(texto_clip)

        t_actual += voz_clip.duration

        silencio_dur = _duracion_silencio_frase(frase)
        silencio = generar_silencio(silencio_dur).set_start(t_actual)

        clips_guiados.append(silencio)
        t_actual += silencio_dur


    # -----------------------
    # SILENCIO FINAL CONTROLADO
    # -----------------------

    silencio_final = generar_silencio(SILENCIO_FINAL).set_start(t_actual)
    clips_guiados.append(silencio_final)
    t_actual += SILENCIO_FINAL

    # -----------------------
    # TEXTO EN PANTALLA (CON FADE IN / OUT)
    # -----------------------

    clips_texto = []
    t = dur_voz_titulo + 1.0

    for i, (p, dur_p) in enumerate(zip(parrafos, duraciones), start=1):
        crear_imagen_texto(p, f"bloque_{i}.png")

        onscreen = dur_voz_intro if i == 1 else min(
            max(TEXTO_ONSCREEN_MIN, dur_p * 0.25),
            TEXTO_ONSCREEN_MAX
        )

        c = (
            ImageClip(f"bloque_{i}.png")
            .set_duration(onscreen)
            .set_start(t)
            .set_position("center")
            .fx(fadein, FADE_TEXTO_IN)
            .fx(fadeout, FADE_TEXTO_OUT)
        )

        clips_texto.append(c)
        t += dur_p

    # -----------------------
    # AUDIO FINAL
    # -----------------------

    audio_duracion = max(t_actual, dur_total) + CTA_DUR

    musica_clip, musica_usada = crear_audio(audio_duracion, musica_fija)
    musica_clip = volumex(musica_clip, 0.18)

    audio_final = CompositeAudioClip(
        [musica_clip, voz_titulo, voz_intro] + clips_guiados
    ).set_duration(audio_duracion)

    # -----------------------
    # RENDER
    # -----------------------

    componer_video(
        fondo=fondo,
        grad=grad,
        titulo_clip=titulo_clip,
        audio=audio_final,
        clips_texto=clips_texto + clips_texto_guiado,
        salida=path_out
    )

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    if not modo_test:
        insert_video({
            "id": video_id,
            "channel_id": 7,
            "archivo": path_out,
            "tipo": "long",
            "musica": musica_usada,
            "licencia": licencia_path,
            "imagen": imagen_usada,
            "texto_base": texto,
            "fingerprint": generar_fingerprint_contenido(
                tipo="long",
                texto=texto,
                imagen=imagen_usada,
                musica=musica_usada,
                duracion=int(audio_duracion)
            ),
            "metadata": {
                "guion_guiado_id": guion_id,
                "guion_guiado_frases": guion_guiado
            }
        })

    limpiar_temporales()

if __name__ == "__main__":
    print(
        "Este módulo no se ejecuta directamente.\n"
        "Usa:\n"
        "  python entrypoint.py <cantidad> oracion_long [test]"
    )