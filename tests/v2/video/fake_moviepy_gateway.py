# tests/v2/video/fake_moviepy_gateway.py

class FakeClip:
    def __init__(self, duration=10):
        self.duration = duration

    def set_audio(self, audio):
        return self

    def set_start(self, t):
        return self

    def set_duration(self, d):
        self.duration = d
        return self

    def set_position(self, pos):
        return self

    def set_opacity(self, o):
        return self


class FakeMoviePyGateway:
    def __init__(self):
        self.composited = []
        self.concatenated = []
        self.written = []

    def composite(self, clips):
        self.composited.append(clips)
        return FakeClip()

    def concat(self, clips):
        self.concatenated.append(clips)
        return FakeClip()

    def write(self, clip, path, fps):
        self.written.append((path, fps))
