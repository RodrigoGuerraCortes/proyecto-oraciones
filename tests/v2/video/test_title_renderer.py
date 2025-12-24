# tests/v2/video/test_title_renderer.py

from pathlib import PosixPath
from unittest.mock import MagicMock, patch
from generator.v2.video.title_renderer import render_title_layer, TitleStyle


@patch("generator.v2.video.title_renderer.Image")
def test_render_title_layer(mock_image):
    img = MagicMock()
    draw = MagicMock()
    mock_image.new.return_value = img
    mock_image.Draw.return_value = draw

    style = TitleStyle()

    render_title_layer(
        title="Titulo de prueba",
        output_path="out.png",
        style=style,
    )

    img.save.assert_called_once_with(PosixPath("out.png"))
