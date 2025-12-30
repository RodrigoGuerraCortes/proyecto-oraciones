# generator/v3/adapter/audio_adapter.py

from generator.audio.selector import crear_audio as crear_audio_v1


def crear_audio_v3(
    *,
    duracion: float,
    usar_tts: bool,
    texto_tts: str | None,
):
    """
    Adapter v3 → v1 para audio.

    NOTAS:
    - v1 controla:
        - selección de música
        - acceso a DB
        - paths ('musica/')
        - mezcla voz + música
    - v3 solo decide SI hay TTS o no.
    """

    return crear_audio_v1(
        duracion=duracion,
        musica_fija=None,
        usar_tts=usar_tts,
        texto_tts=texto_tts,
    )
