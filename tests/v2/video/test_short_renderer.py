# tests/v2/video/test_short_renderer.py

from unittest.mock import patch, MagicMock

from generator.v2.video.short_renderer import (
    render_short,
    ShortRenderConfig,
)
from generator.v2.video.background_renderer import BackgroundConfig
from generator.v2.video.title_renderer import TitleStyle
from generator.v2.video.text_renderer import TextStyle

from generator.v2.audio.models import AudioRequest
from generator.v2.content.parser import ParsedContent, ContentBlock


def fake_parsed_content():
    return ParsedContent(
        title="Titulo",
        blocks=[
            ContentBlock(text="Linea 1"),
            ContentBlock(text="Linea 2"),
        ]
    )


#@patch("generator.v2.video.short_renderer.cleanup_temp_files")
#@patch("generator.v2.video.short_renderer.compose_video")
#@patch("generator.v2.video.short_renderer.build_audio")
@patch("generator.v2.video.short_renderer.render_text_layer")
@patch("generator.v2.video.short_renderer.render_title_layer")
@patch("generator.v2.video.short_renderer.render_background")
@patch("generator.v2.video.short_renderer.ImageClip")
def test_render_short_happy_path(
    mock_imageclip,
    mock_render_background,
    mock_render_title,
    mock_render_text,
    mock_build_audio,
    mock_compose,
    mock_cleanup,
):
    fake_clip = MagicMock()
    fake_clip.set_duration.return_value = fake_clip
    fake_clip.set_position.return_value = fake_clip
    fake_clip.set_opacity.return_value = fake_clip
    fake_clip.set_start.return_value = fake_clip
    mock_imageclip.return_value = fake_clip
    # -------------------------------------------------
    # Arrange
    # -------------------------------------------------
    parsed = fake_parsed_content()

    fondo = MagicMock()
    grad = MagicMock()
    mock_render_background.return_value = (fondo, grad)

    audio_clip = MagicMock()
    mock_build_audio.return_value = MagicMock(
        audio_clip=audio_clip,
        music_used="music.mp3",
    )

    audio_req = AudioRequest(
        duration=0,
        tts_enabled=True,
        tts_text="texto",
        music_enabled=True,
    )

    config = ShortRenderConfig(
        max_lines=5,
        cta_seconds=5,
    )

    background_cfg = BackgroundConfig()
    title_style = TitleStyle()
    text_style = TextStyle()

    # -------------------------------------------------
    # Act
    # -------------------------------------------------
    result = render_short(
        parsed=parsed,
        output_path="out.mp4",
        image_path="image.jpg",
        audio_req=audio_req,
        config=config,
        background_cfg=background_cfg,
        title_style=title_style,
        text_style=text_style,
        cta_image_path=None,
        modo_test=True,
    )

    # -------------------------------------------------
    # Assert – renderers
    # -------------------------------------------------
    mock_render_background.assert_called_once()
    mock_render_title.assert_called_once()
    assert mock_render_text.call_count == len(parsed.blocks)

    # -------------------------------------------------
    # Assert – audio
    # -------------------------------------------------
    #mock_build_audio.assert_called_once()
    #assert audio_req.duration > 0

    # -------------------------------------------------
    # Assert – composer
    # -------------------------------------------------
    mock_compose.assert_called_once()
    args, kwargs = mock_compose.call_args
    request = kwargs["request"]

    assert request.output_path == "out.mp4"
    assert len(request.base_layers) == 2
    assert request.audio == audio_clip

    # -------------------------------------------------
    # Assert – cleanup
    # -------------------------------------------------
    #mock_cleanup.assert_called_once()

    # -------------------------------------------------
    # Assert – resultado
    # -------------------------------------------------
    assert result["output"] == "out.mp4"
    assert result["has_voice"] is True
