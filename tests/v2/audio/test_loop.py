# tests/v2/audio/test_loop.py

from unittest.mock import MagicMock
from generator.v2.audio.loop import build_loop_clips


def test_audio_loop_extends_audio():
    audio = MagicMock()
    audio.duration = 2

    sub = MagicMock()
    sub.duration = 2
    audio.subclip.return_value = sub

    clips = build_loop_clips(audio, 5)

    # 2 + 2 + 1 = 5 → 3 clips
    assert len(clips) == 3
