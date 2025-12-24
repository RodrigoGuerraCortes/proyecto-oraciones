# tests/v2/audio/test_tts_engine.py

import pytest
from unittest.mock import patch
from generator.v2.audio.tts_engine import generate_voice


def test_generate_voice_empty_text():
    with pytest.raises(ValueError):
        generate_voice("", "tmp/test.wav")


@patch("generator.v2.audio.tts_engine.subprocess.run")
@patch("generator.v2.audio.tts_engine.AudioFileClip")
def test_generate_voice_ok(mock_audio, mock_run, tmp_path):
    wav = tmp_path / "voice.wav"
    mock_audio.return_value = "audio_clip"

    clip = generate_voice("Hola", str(wav))

    assert clip == "audio_clip"
    mock_run.assert_called_once()
