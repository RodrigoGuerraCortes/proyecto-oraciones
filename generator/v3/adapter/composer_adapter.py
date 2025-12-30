# generator/v3/adapter/composer_adapter.py

from generator.video.composer import componer_video as componer_video_v1


def componer_video_v3(
    *,
    fondo,
    grad,
    titulo_clip,
    audio,
    text_clips,
    output_path,
):
    # NO offsets
    return componer_video_v1(
        fondo,
        grad,
        titulo_clip,
        audio,
        text_clips,
        output_path,
    )