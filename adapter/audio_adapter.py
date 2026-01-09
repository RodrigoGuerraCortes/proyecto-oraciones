# adapter/audio_adapter.py

from generator.audio.selector import crear_audio


def crear_audio_v3(
    *,
    duracion: float,
    usar_tts: bool,
    texto_tts: str | None,
    music_path: str,
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

    return crear_audio(
        duracion=duracion,
        musica_fija=None,
        usar_tts=usar_tts,
        texto_tts=texto_tts,
        music_path=music_path,
    )
