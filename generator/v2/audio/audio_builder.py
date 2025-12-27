# generator/v2/audio/audio_builder.py

from generator.v2.audio.models import AudioRequest, AudioResult
from generator.v2.audio.music_selector import select_music
from generator.v2.audio.tts_engine import generate_voice
from generator.v2.audio.silence import generate_silence
from moviepy.editor import CompositeAudioClip, AudioFileClip, concatenate_audioclips
import uuid
import os


DUCKING_FACTOR = 0.35  # 35 % del volumen original

def build_audio(req: AudioRequest) -> AudioResult:

    print(
        "[AUDIO-BUILD] "
        f"duration={req.duration:.2f}s | "
        f"music={req.music_enabled} | "
        f"tts={req.tts_enabled} | "
        f"blocks={len(req.tts_blocks) if req.tts_blocks else 0}"
    )

    music_clip = None
    music_used = None

    if req.music_enabled:
        music_clip, music_used = select_music(
            duration=req.duration,
            base_path=req.music_base_path,
            fixed=req.music_fixed
        )

        print(
            f"[MUSIC] file={music_used} | "
            f"base_volume={req.music_volume:.2f} | "
            f"ducking={'yes' if req.tts_enabled else 'no'}"
        )

        # volumen base
        music_volume = req.music_volume

        # ducking automático si hay TTS
        if req.tts_enabled:
            music_volume *= DUCKING_FACTOR

        music_clip = music_clip.volumex(music_volume)

    if not req.tts_enabled:
        return AudioResult(
            audio_clip=music_clip,
            music_used=music_used
        )
    
    if req.tts_blocks:
        return build_audio_with_blocks(req)

    if not req.tts_text:
        raise ValueError("TTS enabled but no text provided")

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


    print("[AUDIO-BUILD] final audio ready")
    
    return AudioResult(
        audio_clip=final_audio,
        music_used=music_used
    )


def build_audio_with_blocks(req: AudioRequest) -> AudioResult:
    layers = []

    # Música base (ya con ducking aplicado antes)
    music_clip = None
    music_used = None

    if req.music_enabled:
        music_clip, music_used = select_music(
            duration=req.duration,
            base_path=req.music_base_path,
            fixed=req.music_fixed,
        )

        base_volume = req.music_volume
        music_clip = music_clip.volumex(base_volume)
        layers.append(music_clip)

    # Voz por bloque
    for block in req.tts_blocks:

        print(
            f"[TTS-BLOCK] "
            f"start={block.start:.2f}s | "
            f"duration={block.duration:.2f}s | "
            f"text_len={len(block.text)}"
        )

        tts_path = f"tmp/tts/{uuid.uuid4().hex}.wav"
        voice = generate_voice(block.text, salida_wav=tts_path)

        # ajustar duración exacta
        if voice.duration > block.duration:
            voice = voice.subclip(0, block.duration)
        else:
            voice = CompositeAudioClip([
                voice,
                generate_silence(block.duration - voice.duration)
            ])

        voice = (
            voice.volumex(req.voice_volume)
                 .set_start(block.start)
        )

        layers.append(voice)

    final_audio = CompositeAudioClip(layers)

    return AudioResult(
        audio_clip=final_audio,
        music_used=music_used,
    )