# generator/v3/adapter/tts_adapter.py

from moviepy.editor import AudioFileClip
from generator.v3.generator.audio.tts_edge import generar_voz_edge
import uuid

def crear_tts_v3(*, texto: str, engine: str) -> AudioFileClip:
    """
    Genera TTS y devuelve el AudioClip resultante.
    Fuente de verdad para la duración del video cuando hay voz.
    """

    tts_path = f"tmp/tts_{uuid.uuid4().hex}.wav"

    result = generar_voz_edge(
        texto=texto,
        salida_wav=tts_path,
    )

    if isinstance(result, AudioFileClip):
        audio = result
    else:
        audio = AudioFileClip(result)

    print(f"[TTS] generado duración={audio.duration:.2f}s engine={engine}")

    return audio
