# generator/v3/adapter/audio_plain_adapter.py

from moviepy.editor import CompositeAudioClip
from generator.v3.adapter.tts_adapter import crear_tts_v3
from generator.v3.adapter.audio_adapter import crear_audio_v3


def crear_audio_plain_v3(
    *,
    texto: str,
    usar_tts: bool,
    music_path: str,
    tts_engine: str,
    cta_seconds: float = 0,
):
    """
    Audio exclusivo para formatos PLAIN.
    Flujo:
      1. Decide si usar TTS
      2. Genera música
      3. Une TTS + música
    """

    print("[AUDIO_PLAIN] ===== inicio =====")
    print(f"[AUDIO_PLAIN] usar_tts={usar_tts}")

    # -------------------------------------------------
    # 1️⃣ TTS (opcional)
    # -------------------------------------------------
    tts_audio = None
    duracion_base = None

    if usar_tts:
        print("[AUDIO_PLAIN] generando TTS")

        tts_audio = crear_tts_v3(
            texto=texto,
            engine=tts_engine,
        )

        duracion_base = tts_audio.duration

        print(f"[AUDIO_PLAIN][TTS] duración={duracion_base:.2f}s")

    # -------------------------------------------------
    # 2️⃣ Música (usa motor existente)
    # -------------------------------------------------
    print("[AUDIO_PLAIN] generando música")

    musica_audio, musica_usada = crear_audio_v3(
        duracion=duracion_base,
        usar_tts=False,          # 👈 IMPORTANTE: aquí solo música
        texto_tts=None,
        music_path=music_path,
    )

    print(
        f"[AUDIO_PLAIN][MUSIC] duración={musica_audio.duration:.2f}s "
        f"archivo={musica_usada}"
    )

    # -------------------------------------------------
    # 3️⃣ Unión final
    # -------------------------------------------------
    if tts_audio:
        print("[AUDIO_PLAIN] uniendo TTS + música")

        audio_final = CompositeAudioClip(
            [musica_audio, tts_audio.set_start(0)]
        )

    else:
        print("[AUDIO_PLAIN] solo música (sin TTS)")
        audio_final = musica_audio

    print(f"[AUDIO_PLAIN] duración_final={audio_final.duration:.2f}s")
    print("[AUDIO_PLAIN] ===== fin =====")

    return audio_final, musica_usada
