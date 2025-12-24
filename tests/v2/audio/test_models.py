# tests/v2/audio/test_models.py

from generator.v2.audio.models import AudioRequest, AudioResult


def test_audio_request_defaults():
    req = AudioRequest(duration=10)

    assert req.duration == 10
    assert req.music_enabled is True
    assert req.tts_enabled is False
    assert req.music_volume == 0.35


def test_audio_result_container():
    dummy_clip = object()
    res = AudioResult(audio_clip=dummy_clip, music_used="test.mp3")

    assert res.audio_clip is dummy_clip
    assert res.music_used == "test.mp3"
