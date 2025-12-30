# generator/v2/pipeline/audio/tts_prepare.py

from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import AudioRequest

def prepare_tts_if_needed(
    *,
    audio_req: AudioRequest,
    parsed_blocks,
    content_cfg: dict,
):
    """
    Prepara TTS (texto + preview real) si audio_req.tts_enabled=True
    Idempotente: se puede llamar múltiples veces sin romper estado.
    """

    if not audio_req.tts_enabled:
        content_cfg["_tts_enabled"] = False
        content_cfg.pop("_tts_duration", None)
        return

    # Si ya está preparado, no repetir
    if audio_req.tts_text is not None or audio_req.tts_blocks is not None:
        return

    full_text = "\n\n".join(b.text for b in parsed_blocks)

    audio_req.tts_text = full_text
    audio_req.tts_blocks = None

    preview_req = AudioRequest(
        duration=999.0,
        tts_enabled=True,
        tts_text=full_text,
        music_enabled=False,
    )

    preview_audio = build_audio(preview_req)

    content_cfg["_tts_enabled"] = True
    content_cfg["_tts_duration"] = preview_audio.tts_duration
