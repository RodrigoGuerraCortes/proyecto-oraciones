# generator/v2/audio/audio_builder.py

from __future__ import annotations

import os
import uuid
from moviepy.editor import (
    CompositeAudioClip,
    concatenate_audioclips,
)

from generator.v2.audio.models import AudioRequest, AudioResult
from generator.v2.audio.music_selector import select_music
from generator.v2.audio.tts_engine import generate_voice
from generator.v2.audio.silence import generate_silence
from generator.audio.loop import audio_loop   # reutilizado desde v1

DUCKING_FACTOR = 0.35  # 35 % del volumen base


def build_audio(req: AudioRequest) -> AudioResult:
    """
    Build de audio para SHORT / PLAIN / LONG
    - TTS dura req.duration
    - Música dura req.music_duration (o req.duration si no se define)
    """

    print(
        "[AUDIO-BUILD] "
        f"duration={req.duration:.2f}s | "
        f"music={req.music_enabled} | "
        f"tts={req.tts_enabled} | "
        f"blocks={len(req.tts_blocks) if req.tts_blocks else 0}"
    )

    print(
        "[AUDIO-IN] "
        f"req.duration={req.duration} | req.music_duration={req.music_duration} | "
        f"computed_music_duration={(req.music_duration or req.duration)} | "
        f"music_enabled={req.music_enabled} | tts_enabled={req.tts_enabled} | "
        f"music_base_path={req.music_base_path} | fixed={req.music_fixed}"
    )


    music_clip = None
    music_used = None

    # -------------------------
    # Duraciones
    # -------------------------
    music_duration = req.music_duration or req.duration

    # -------------------------
    # Música base
    # -------------------------
    if req.music_enabled:
        music_clip, music_used = select_music(
            duration=music_duration,
            base_path=req.music_base_path,
            fixed=req.music_fixed,
        )

        print(
            "[AUDIO-MUSIC] "
            f"selected={music_used} | "
            f"raw_music_clip.duration={music_clip.duration:.2f}s | "
            f"target_music_duration={music_duration:.2f}s"
        )

        # Loop / trim EXACTO (V1 behavior)
        if music_clip.duration < music_duration:
            music_clip = audio_loop(music_clip, music_duration)
        else:
            music_clip = music_clip.subclip(0, music_duration)

        print(
            f"[MUSIC] file={music_used} | "
            f"base_volume={req.music_volume:.2f} | "
            f"ducking={'yes' if req.tts_enabled else 'no'}"
        )

        music_volume = req.music_volume
        if req.tts_enabled:
            music_volume *= DUCKING_FACTOR

        music_clip = music_clip.volumex(music_volume)

    # -------------------------
    # Sin TTS → solo música
    # -------------------------
    if not req.tts_enabled:
        final_audio = music_clip.set_duration(music_duration) if music_clip else None

        return AudioResult(
            audio_clip=final_audio,
            music_used=music_used,
        )

    # -------------------------
    # TTS por bloques
    # -------------------------
    if req.tts_blocks:
        return build_audio_with_blocks(req)

    # -------------------------
    # TTS continuo
    # -------------------------
    if not req.tts_text:
        raise ValueError("TTS enabled but no text provided")

    tts_dir = "tmp/tts"
    os.makedirs(tts_dir, exist_ok=True)

    tts_path = f"{tts_dir}/{uuid.uuid4().hex}.wav"

    voice_clip = generate_voice(
        texto=req.tts_text,
        salida_wav=tts_path,
    )

    print(
        "[AUDIO-VOICE] "
        f"generated_voice.duration={voice_clip.duration:.2f}s | "
        f"target_tts_duration(req.duration)={req.duration:.2f}s"
    )

    tts_duration_real = voice_clip.duration

    # Ajuste exacto a duración TTS (NO CTA)
    if voice_clip.duration < req.duration:
        voice_clip = concatenate_audioclips([
            voice_clip,
            generate_silence(req.duration - voice_clip.duration),
        ])
    else:
        voice_clip = voice_clip.subclip(0, req.duration)

    voice_clip = voice_clip.volumex(req.voice_volume)

    print(
        "[AUDIO-VOICE] "
        f"after_fit_to_req.duration={voice_clip.duration:.2f}s"
    )

    # -------------------------
    # Mezcla final
    # -------------------------
    if music_clip:
        final_audio = CompositeAudioClip([music_clip, voice_clip])
    else:
        final_audio = voice_clip


    print(
        "[AUDIO-MIX] "
        f"pre_set_duration.final_audio.duration={final_audio.duration:.2f}s | "
        f"music_duration={music_duration:.2f}s | "
        f"music_clip.duration={(music_clip.duration if music_clip else None)}"
    )

    final_audio = final_audio.set_duration(music_duration)


    print(
        "[AUDIO-MIX] "
        f"post_set_duration.final_audio.duration={final_audio.duration:.2f}s"
    )

    print("[AUDIO-BUILD] final audio ready")

    return AudioResult(
        audio_clip=final_audio,
        music_used=music_used,
        tts_duration=tts_duration_real,
    )


def build_audio_with_blocks(req: AudioRequest) -> AudioResult:
    """
    Build de audio con múltiples bloques TTS.
    Soporta CTA extendiendo música.
    """

    layers = []

    music_clip = None
    music_used = None

    music_duration = req.music_duration or req.duration

    # -------------------------
    # Música base
    # -------------------------
    if req.music_enabled:
        music_clip, music_used = select_music(
            duration=music_duration,
            base_path=req.music_base_path,
            fixed=req.music_fixed,
        )

        if music_clip.duration < music_duration:
            music_clip = audio_loop(music_clip, music_duration)
        else:
            music_clip = music_clip.subclip(0, music_duration)

        music_volume = req.music_volume
        if req.tts_enabled:
            music_volume *= DUCKING_FACTOR

        music_clip = music_clip.volumex(music_volume)
        layers.append(music_clip)

    # -------------------------
    # Voz por bloque
    # -------------------------
    for block in req.tts_blocks:
        print(
            f"[TTS-BLOCK] "
            f"start={block.start:.2f}s | "
            f"duration={block.duration:.2f}s | "
            f"text_len={len(block.text)}"
        )

        tts_path = f"tmp/tts/{uuid.uuid4().hex}.wav"
        voice = generate_voice(block.text, salida_wav=tts_path)

        if voice.duration > block.duration:
            voice = voice.subclip(0, block.duration)
        else:
            voice = concatenate_audioclips([
                voice,
                generate_silence(block.duration - voice.duration),
            ])

        voice = (
            voice.volumex(req.voice_volume)
                 .set_start(block.start)
        )

        layers.append(voice)

    final_audio = CompositeAudioClip(layers).set_duration(music_duration)

    return AudioResult(
        audio_clip=final_audio,
        music_used=music_used,
    )
