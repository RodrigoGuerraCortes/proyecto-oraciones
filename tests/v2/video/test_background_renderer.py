# tests/v2/video/test_background_renderer.py

from unittest.mock import MagicMock, patch
from generator.v2.video.background_renderer import (
    render_background,
    BackgroundConfig,
)


@patch("generator.v2.video.background_renderer.Image")
@patch("generator.v2.video.background_renderer.ImageClip")
def test_render_background_happy_path(mock_imageclip, mock_image):
    pil = MagicMock()
    pil.convert.return_value = pil
    pil.resize.return_value = pil
    pil.filter.return_value = pil
    pil.save.return_value = None
    pil.convert.return_value.resize.return_value.getdata.return_value = [50] * 100

    mock_image.open.return_value = pil
    mock_image.new.return_value = pil
    mock_image.blend.return_value = pil

    clip = MagicMock()
    clip.set_duration.return_value = clip
    clip.resize.return_value = clip
    mock_imageclip.return_value = clip

    config = BackgroundConfig()

    fondo, grad = render_background(
        image_path="fake.jpg",
        duration=5,
        config=config,
    )

    assert fondo is clip
    assert grad is clip
