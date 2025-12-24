# tests/v2/video/test_text_renderer.py

from unittest.mock import MagicMock, patch
from generator.v2.video.text_renderer import render_text_layer, TextStyle


@patch("generator.v2.video.text_renderer.Image")
def render_text_layer(mock_image):
    img = MagicMock()
    draw = MagicMock()
    mock_image.new.return_value = img
    mock_image.Draw.return_value = draw

    style = TextStyle()

    render_text_layer(
        lines=["Linea 1", "Linea 2"],
        output_path="text.png",
        style=style,
    )

    img.save.assert_called_once_with("text.png")
