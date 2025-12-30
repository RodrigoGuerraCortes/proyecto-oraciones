# generator/v3/audio/stanza_tts_builder.py

from moviepy.editor import CompositeAudioClip, concatenate_audioclips, AudioFileClip
from generator.audio.tts_edge import generar_voz_edge
from generator.audio.silence import generar_silencio


def construir_audio_stanza_tts(
    *,
    titulo: str,
    estrofas: list[str],
    musica_path: str | None,
    pause_after_title: float,
    pause_between_blocks: float,
):
    """
    Replica EXACTA del comportamiento v1 para salmos:
    - Voz del título
    - Silencio
    - Voz por estrofa
    - Silencio entre estrofas
    - Música de fondo continua
    """

    voces = []
    duraciones = []

    # -------------------------------------------------
    # Título hablado
    # -------------------------------------------------
    voz_titulo = generar_voz_edge(titulo)
    voces.append(voz_titulo)
    duraciones.append(voz_titulo.duration)

    if pause_after_title > 0:
        silencio = generar_silencio(pause_after_title)
        voces.append(silencio)
        duraciones.append(pause_after_title)

    # -------------------------------------------------
    # Estrofas habladas
    # -------------------------------------------------
    for idx, estrofa in enumerate(estrofas):
        voz = generar_voz_edge(estrofa)
        voces.append(voz)
        duraciones.append(voz.duration)

        if idx < len(estrofas) - 1 and pause_between_blocks > 0:
            silencio = generar_silencio(pause_between_blocks)
            voces.append(silencio)
            duraciones.append(pause_between_blocks)

    voz_compuesta = concatenate_audioclips(voces)

    # -------------------------------------------------
    # Música de fondo
    # -------------------------------------------------
    if musica_path:
        musica = AudioFileClip(musica_path).set_duration(voz_compuesta.duration)
        audio_final = CompositeAudioClip([musica, voz_compuesta])
    else:
        audio_final = voz_compuesta

    return audio_final, voz_compuesta.duration, duraciones
