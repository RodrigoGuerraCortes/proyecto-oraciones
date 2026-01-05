# generator/v3/adapter/composer_adapter.py

from generator.v3.generator.composer import componer_video


def componer_video_v3(
    *,
    fondo,
    grad,
    titulo_clip,
    audio,
    text_clips,
    output_path,
    visual_cfg: dict | None = None,
    cta_cfg: dict | None = None,
    base_path_assest: str,
):
    # NO offsets
    return componer_video(
        fondo,
        grad,
        titulo_clip,
        audio,
        text_clips,
        output_path,
        visual_cfg=visual_cfg,
        cta_cfg=cta_cfg,
        base_path_assest=base_path_assest,
    )