# generator/v2/video/moviepy_gateway.py

from moviepy.editor import CompositeVideoClip, concatenate_videoclips


class MoviePyGateway:
    """
    Interfaz abstracta (conceptual).
    """

    def composite(self, clips):
        raise NotImplementedError

    def concat(self, clips):
        raise NotImplementedError

    def write(self, clip, path: str, fps: int):
        raise NotImplementedError


class MoviePyGatewayImpl(MoviePyGateway):
    """
    Implementación real con MoviePy.
    """

    def composite(self, clips):
        return CompositeVideoClip(clips)

    def concat(self, clips):
        return concatenate_videoclips(clips)

    def write(self, clip, path: str, fps: int):
        clip.write_videofile(
            path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
        )
