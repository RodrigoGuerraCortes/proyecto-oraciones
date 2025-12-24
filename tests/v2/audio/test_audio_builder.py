# tests/v2/audio/test_audio_builder.py

from unittest.mock import MagicMock, patch
from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import AudioRequest

@patch("generator.v2.audio.audio_builder.select_music")
def test_build_audio_music_only(mock_select_music):
    music_clip = MagicMock()
    music_clip.volumex.return_value = music_clip

    mock_select_music.return_value = (music_clip, "music.mp3")

    req = AudioRequest(
        duration=10,
        music_enabled=True,
        tts_enabled=False
    )

    result = build_audio(req)

    mock_select_music.assert_called_once()
    assert result.audio_clip == music_clip
    assert result.music_used == "music.mp3"



@patch("generator.v2.audio.audio_builder.generate_voice")
def test_build_audio_tts_only(mock_generate_voice):
    voice_clip = MagicMock()
    voice_clip.duration = 5
    voice_clip.volumex.return_value = voice_clip
    voice_clip.subclip.return_value = voice_clip

    mock_generate_voice.return_value = voice_clip

    req = AudioRequest(
        duration=5,
        music_enabled=False,
        tts_enabled=True,
        tts_text="Hola mundo"
    )

    result = build_audio(req)

    
    assert mock_generate_voice.call_count == 1

    args, kwargs = mock_generate_voice.call_args

    assert kwargs["texto"] == "Hola mundo"
    assert kwargs["salida_wav"].startswith("tmp/tts/")
    assert kwargs["salida_wav"].endswith(".wav")

    assert result.audio_clip == voice_clip
    assert result.music_used is None




@patch("generator.v2.audio.audio_builder.CompositeAudioClip")
@patch("generator.v2.audio.audio_builder.generate_voice")
@patch("generator.v2.audio.audio_builder.select_music")
def test_build_audio_music_and_tts(
    mock_select_music,
    mock_generate_voice,
    mock_composite
):
    # --- mocks ---
    music_clip = MagicMock()
    music_clip.volumex.return_value = music_clip

    voice_clip = MagicMock()
    voice_clip.duration = 3
    voice_clip.volumex.return_value = voice_clip
    voice_clip.subclip.return_value = voice_clip

    composite_result = MagicMock()
    mock_composite.return_value = composite_result

    mock_select_music.return_value = (music_clip, "bg.mp3")
    mock_generate_voice.return_value = voice_clip

    req = AudioRequest(
        duration=3,
        music_enabled=True,
        tts_enabled=True,
        tts_text="Texto TTS"
    )

    # --- act ---
    result = build_audio(req)

    # --- assert ---
    mock_select_music.assert_called_once()
    
    assert mock_generate_voice.call_count == 1

    args, kwargs = mock_generate_voice.call_args

    assert kwargs["texto"] == "Texto TTS"
    assert kwargs["salida_wav"].startswith("tmp/tts/")

    mock_composite.assert_called_once_with([music_clip, voice_clip])

    assert result.audio_clip == composite_result
    assert result.music_used == "bg.mp3"
