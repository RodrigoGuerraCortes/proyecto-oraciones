import uuid
import os

from generator.v2.content.selector_simple import elegir_texto_simple
from generator.v2.content.parser import parse_content

from generator.v2.video.short_renderer import render_short
from generator.v2.pipeline.config_resolver import resolve_short_config


def run_short_pipeline(
    *,
    channel_config: dict,
    channel_id: int,
    format_code: str,
    quantity: int,
    modo_test: bool = False,
):
    """
    Pipeline genérico para SHORTS v2.
    """

    assert format_code in channel_config["formats"]

    fmt = channel_config["formats"][format_code]

    base_path = channel_config["content"]["base_path"]
    content_path = fmt["content"]["path"]
    mode = fmt["content"]["type"]            # "plain" | "stanzas"
    max_blocks = fmt["content"].get("max_blocks")

    output_dir = (
        f"videos/test/{format_code}"
        if modo_test
        else f"videos/{format_code}"
    )
    os.makedirs(output_dir, exist_ok=True)

    for i in range(quantity):

        # -----------------------------------
        # 1) Selección de contenido (filesystem)
        # -----------------------------------
        path_txt, base_name = elegir_texto_simple(
            base_path=base_path,
            sub_path=content_path,
        )

        # -----------------------------------
        # 2) Lectura del archivo
        # -----------------------------------
        with open(path_txt, "r", encoding="utf-8") as f:
            raw_text = f.read()

        title = base_name.replace("_", " ").strip()

        # -----------------------------------
        # 3) Parseo
        # -----------------------------------
        parsed = parse_content(
            raw_text=raw_text,
            title=title,
            mode=mode,
            max_blocks=max_blocks,
        )

        # Texto completo (para TTS)
        full_text = "\n\n".join(b.text for b in parsed.blocks)

        # -----------------------------------
        # 4) Resolver config
        # -----------------------------------
        resolved = resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
        )

        audio_req = resolved["audio_req"]
        audio_req.tts_text = full_text

        # -----------------------------------
        # 5) Imagen base (placeholder por ahora)
        # -----------------------------------
        image_path = "imagenes/vignette.png"

        # -----------------------------------
        # 6) Output
        # -----------------------------------
        video_id = uuid.uuid4().hex[:8]
        output_path = f"{output_dir}/{video_id}__{base_name}.mp4"

        # -----------------------------------
        # 7) Render
        # -----------------------------------
        render_short(
            parsed=parsed,
            output_path=output_path,
            image_path=image_path,
            audio_req=audio_req,
            config=resolved["render_cfg"],
            background_cfg=resolved["background_cfg"],
            title_style=resolved["title_style"],
            text_style=resolved["text_style"],
            cta_image_path=channel_config["branding"]["cta"],
            watermark_path=channel_config["branding"].get("water_mark"),
            modo_test=modo_test,
        )

        print(f"[PIPELINE V2] OK {i+1}/{quantity} → {output_path}")
