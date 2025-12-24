from generator.v2.audio.silence import generate_silence


def test_generate_silence_duration():
    clip = generate_silence(3)
    assert int(clip.duration) == 3
    assert clip.fps == 44100