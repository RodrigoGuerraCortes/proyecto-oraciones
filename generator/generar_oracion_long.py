import os

from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein
from moviepy.audio.fx.volumex import volumex
from moviepy.editor import CompositeAudioClip

from generator.audio.tts_edge import generar_voz_edge, _normalizar_texto_tts
from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.video.composer import componer_video
from generator.content.fingerprinter import generar_fingerprint_contenido
from generator.cleanup import limpiar_temporales
from generator.image.decision import decidir_imagen_video
from db.repositories.video_repo import insert_video, fingerprint_existe_ultimos_dias
from generator.content.guiones.oracion_guiada_base import GUIÓN_ORACION_GUIADA_BASE
from moviepy.editor import concatenate_audioclips
from generator.audio.silence import generar_silencio
from generator.utils.texto import normalizar_titulo_es
# -----------------------
# CONFIGURACIÓN GENERAL
# -----------------------

CTA_DUR = 5

DUR_OBJ_MIN = 180   # 3 min
DUR_OBJ_MAX = 300   # 5 min

TEXTO_ONSCREEN_MIN = 8
TEXTO_ONSCREEN_MAX = 14

VOZ_DIR = "voz"

# Duración reducida solo para test de long
DUR_TEST_LONG = 28   # segundos


# -----------------------
# UTILIDADES INTERNAS
# -----------------------

def _split_parrafos(texto: str) -> list[str]:
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    out = []
    for p in parrafos:
        p = (
            p.replace("senor", "señor")
             .replace("Senor", "Señor")
             .replace("dios", "Dios")
        )
        out.append(p)
    return out


def _word_count(s: str) -> int:
    return len([w for w in s.split() if w.strip()])


def _asignar_duraciones(parrafos: list[str], dur_total: int) -> list[float]:
    if not parrafos:
        return [float(dur_total)]

    counts = [_word_count(p) for p in parrafos]
    total = sum(counts) or 1

    piso = 18.0
    durs = [max(piso, dur_total * (c / total)) for c in counts]

    suma = sum(durs)
    factor = dur_total / suma if suma else 1.0
    durs = [d * factor for d in durs]

    ajuste = dur_total - sum(durs)
    durs[-1] += ajuste

    return durs


# -----------------------
# FUNCIÓN PRINCIPAL
# -----------------------

def generar_oracion_long(
    *,
    video_id,
    path_in: str,
    path_out: str,
    musica_fija: str | None = None,
    duracion_objetivo: int = 240,
    modo_test: bool = False
):
    """
    Genera un video long (3–5 min) de oración.
    Etapa 2A:
      - Voz edge-tts SOLO en el texto inicial
      - Música durante todo el video
    """

    # -----------------------
    # Cargar texto
    # -----------------------

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        raise RuntimeError("Texto de oración vacío")

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    if modo_test:
        dur_total = DUR_TEST_LONG
    else:
        dur_total = max(DUR_OBJ_MIN, min(DUR_OBJ_MAX, int(duracion_objetivo)))


    parrafos = _split_parrafos(texto)
    texto_intro = parrafos[0]

    if modo_test:
        # en test solo mostramos el texto inicial
        parrafos = [texto_intro]

    duraciones = _asignar_duraciones(parrafos, dur_total)

    # -----------------------
    # Imagen / fondo
    # -----------------------

    imagen_usada = decidir_imagen_video(
        tipo="oracion_long",
        titulo=titulo,
        texto=texto
    )

    fondo, grad = crear_fondo(dur_total, imagen_usada)

    titulo = normalizar_titulo_es(titulo)
    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = (
        ImageClip("titulo.png")
        .set_duration(dur_total)
        .set_position(("center", 120))
        .set_opacity(1)
    )


    os.makedirs(VOZ_DIR, exist_ok=True)

    voz_intro_path = os.path.join(VOZ_DIR, f"intro_{video_id}.wav")

    

    texto_tts = _normalizar_texto_tts(texto_intro)

    voz_intro_clip = generar_voz_edge(
        texto=texto_tts,
        salida_wav=voz_intro_path
    ).set_start(0)

    dur_voz_intro = voz_intro_clip.duration

    # -----------------------
    # VOZ GUIADA (ORACIÓN ACOMPAÑADA)
    # -----------------------

    clips_guiados = []

    t_inicio_guiada = dur_voz_intro + 2.0  # pausa tras la oración base
    t_actual = t_inicio_guiada

    for idx, frase in enumerate(GUIÓN_ORACION_GUIADA_BASE, start=1):
        voz_guiada_path = os.path.join(
            VOZ_DIR, f"guiada_{video_id}_{idx}.wav"
        )

        voz_guiada_clip = generar_voz_edge(
            texto=_normalizar_texto_tts(frase),
            salida_wav=voz_guiada_path
        ).set_start(t_actual)

        clips_guiados.append(voz_guiada_clip)
        t_actual += voz_guiada_clip.duration

        # silencio contemplativo (clave para retención)
        silencio_clip = generar_silencio(3.0).set_start(t_actual)
        clips_guiados.append(silencio_clip)
        t_actual += 3.0

    dur_fin_guiada = t_actual


    # -----------------------
    # Texto en pantalla (bloques)
    # -----------------------

    clips = []
    t = 0.0

    for i, (p, dur_p) in enumerate(zip(parrafos, duraciones), start=1):
        tmp_png = f"bloque_long_{i}.png"
        crear_imagen_texto(p, tmp_png)

        if i == 1:
            # el texto del intro dura exactamente lo mismo que la voz
            onscreen = dur_voz_intro
        else:
            onscreen = min(
                max(TEXTO_ONSCREEN_MIN, dur_p * 0.25),
                TEXTO_ONSCREEN_MAX
            )

        c = (
            ImageClip(tmp_png)
            .set_duration(onscreen)
            .set_start(t)
            .set_position("center")
            .set_opacity(1)
        )

        if not modo_test:
            c = c.fx(fadein, 0.9)

        clips.append(c)
        t += dur_p

    # -----------------------
    # AUDIO FINAL
    # -----------------------

    audio_duracion = dur_total + CTA_DUR

    musica_clip, musica_usada = crear_audio(audio_duracion, musica_fija)
    musica_clip = volumex(musica_clip, 0.18)

    audio_final = CompositeAudioClip(
        [musica_clip, voz_intro_clip] + clips_guiados
    ).set_duration(audio_duracion)

    # -----------------------
    # Fingerprint / persistencia
    # -----------------------

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    fingerprint = generar_fingerprint_contenido(
        tipo="oracion_long",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=int(round(audio_duracion))
    )

    intentos = 0
    while fingerprint_existe_ultimos_dias(fingerprint) and intentos < 5:
        print("⚠ Contenido duplicado → cambiando música")
        musica_clip, musica_usada = crear_audio(audio_duracion, None)
        musica_clip = volumex(musica_clip, 0.18)

        if modo_test:
            audio_final = musica_clip
        else:
            audio_final = CompositeAudioClip([
                musica_clip,
                voz_intro_clip
            ]).set_duration(audio_duracion)

        fingerprint = generar_fingerprint_contenido(
            tipo="oracion_long",
            texto=texto,
            imagen=imagen_usada,
            musica=musica_usada,
            duracion=int(round(audio_duracion))
        )
        intentos += 1

    # -----------------------
    # Render final
    # -----------------------

    componer_video(
        fondo=fondo,
        grad=grad,
        titulo_clip=titulo_clip,
        audio=audio_final,
        clips_texto=clips,
        salida=path_out
    )

    if os.path.exists(path_out):
        if modo_test:
            print(f"[TEST] Video long generado: {path_out}")
        else:
            try:
                insert_video({
                    "id": video_id,
                    "channel_id": 7,
                    "archivo": path_out,
                    "tipo": "oracion_long",
                    "musica": musica_usada,
                    "licencia": licencia_path,
                    "imagen": imagen_usada,
                    "texto_base": texto,
                    "fingerprint": fingerprint,
                })
            except Exception:
                os.remove(path_out)
                raise
    else:
        raise RuntimeError(f"No se pudo crear el archivo final: {path_out}")

    limpiar_temporales()


if __name__ == "__main__":
    print(
        "Este módulo no se ejecuta directamente.\n"
        "Usa:\n"
        "  python entrypoint.py <cantidad> oracion_long [test]"
    )
