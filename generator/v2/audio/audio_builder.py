# generator/v2/audio/audio_builder.py

from generator.v2.audio.models import AudioRequest, AudioResult
from generator.v2.audio.music_selector import select_music
from generator.v2.audio.tts_engine import generate_voice
from generator.v2.audio.silence import generate_silence
from moviepy.editor import CompositeAudioClip, concatenate_audioclips


def build_audio(req: AudioRequest) -> AudioResult:
    music_clip = None
    music_used = None

    if req.music_enabled:
        music_clip, music_used = select_music(
            duration=req.duration,
            fixed=req.music_fixed
        )
        music_clip = music_clip.volumex(req.music_volume)

    if not req.tts_enabled:
        return AudioResult(
            audio_clip=music_clip,
            music_used=music_used
        )

    if not req.tts_text:
        raise ValueError("TTS enabled but no text provided")

    import uuid
    import os

    tts_dir = "tmp/tts"
    os.makedirs(tts_dir, exist_ok=True)

    tts_path = f"{tts_dir}/{uuid.uuid4().hex}.wav"

    voice_clip = generate_voice(
        texto=req.tts_text,
        salida_wav=tts_path,
    )

    if voice_clip.duration < req.duration:
        voice_clip = concatenate_audioclips([
            voice_clip,
            generate_silence(req.duration - voice_clip.duration)
        ])
    else:
        voice_clip = voice_clip.subclip(0, req.duration)

    voice_clip = voice_clip.volumex(req.voice_volume)

    if music_clip:
        final_audio = CompositeAudioClip([music_clip, voice_clip])
    else:
        final_audio = voice_clip

    return AudioResult(
        audio_clip=final_audio,
        music_used=music_used
    )
