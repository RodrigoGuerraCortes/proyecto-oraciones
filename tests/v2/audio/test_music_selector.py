# tests/v2/audio/test_music_selector.py

import pytest
from unittest.mock import patch, MagicMock
from generator.v2.audio.music_selector import select_music


@patch("generator.v2.audio.music_selector.os.listdir")
def test_music_selector_no_files(mock_ls):
    mock_ls.return_value = []

    with pytest.raises(RuntimeError):
        select_music(10)


@patch("generator.v2.audio.music_selector.AudioFileClip")
@patch("generator.v2.audio.music_selector.os.listdir")
def test_music_selector_ok(mock_ls, mock_clip):
    mock_ls.return_value = ["a.mp3"]
    mock_clip.return_value.duration = 20

    audio, name = select_music(10)

    assert name == "a.mp3"
