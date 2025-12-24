# tests/v2/video/test_composer.py

# tests/v2/video/test_composer.py

from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import (
    ComposerRequest,
    Overlay,
)
from tests.v2.video.fake_moviepy_gateway import (
    FakeMoviePyGateway,
    FakeClip,
)


def test_compose_video_without_cta():
    gateway = FakeMoviePyGateway()

    fondo = FakeClip(duration=10)
    grad = FakeClip(duration=10)
    titulo = FakeClip(duration=10)
    audio = FakeClip(duration=10)

    request = ComposerRequest(
        base_layers=[fondo, grad],
        overlays=[
            Overlay(
                clip=titulo,
                start=0,
                duration=10,
            )
        ],
        audio=audio,
        cta_layers=None,
        output_path="out.mp4",
    )

    result = compose_video(request=request, gateway=gateway)

    assert result.output_path == "out.mp4"
    assert gateway.written
    assert not gateway.concatenated


def test_compose_video_with_cta():
    gateway = FakeMoviePyGateway()

    fondo = FakeClip(duration=10)
    grad = FakeClip(duration=10)
    texto = FakeClip(duration=10)
    audio = FakeClip(duration=10)
    cta = FakeClip(duration=5)

    request = ComposerRequest(
        base_layers=[fondo, grad],
        overlays=[
            Overlay(
                clip=texto,
                start=0,
                duration=10,
            )
        ],
        audio=audio,
        cta_layers=[cta],
        output_path="out_cta.mp4",
    )

    result = compose_video(request=request, gateway=gateway)

    assert result.output_path == "out_cta.mp4"
    assert gateway.concatenated
