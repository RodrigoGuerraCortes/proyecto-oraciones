# generator/v2/pipeline/short_pipeline.py
import uuid
import os

from generator.v2.content.selector_simple import elegir_texto_simple
from generator.v2.content.parser import parse_content

from generator.v2.video.short_renderer import render_short
from generator.v2.pipeline.config_resolver import resolve_short_config
from generator.v2.video.background_selector.with_history import (
    HistoryBackgroundSelector
)


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
        # 1) Resolver config
        # -----------------------------------
        resolved = resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
        )

        base_path = resolved["content_base_path"]

        # -----------------------------------
        # 2) Selección de contenido (filesystem)
        # -----------------------------------
        path_txt, base_name = elegir_texto_simple(
            base_path=base_path,
            sub_path=content_path,
        )


        # -----------------------------------
        # 3) Lectura del archivo
        # -----------------------------------
        with open(path_txt, "r", encoding="utf-8") as f:
            raw_text = f.read()

        title = base_name.replace("_", " ").strip()

        # -----------------------------------
        # 4) Parseo
        # -----------------------------------
        parsed = parse_content(
            raw_text=raw_text,
            title=title,
            mode=mode,
            max_blocks=max_blocks,
        )

        # Texto completo (para TTS)
        full_text = "\n\n".join(b.text for b in parsed.blocks)



        audio_req = resolved["audio_req"]
        audio_req.tts_text = full_text

        # -----------------------------------
        # 5) Imagen base (background)
        # -----------------------------------
        bg_selector = HistoryBackgroundSelector(
            base_path=resolved["background_selector_cfg"]["base_path"],
            ventana=resolved["background_selector_cfg"]["ventana"],
            fallback=resolved["background_selector_cfg"]["fallback"],
        )

        image_path = bg_selector.elegir(
            text=full_text,
            title=parsed.title,
            format_code=format_code,
            channel_id=channel_id,
        )


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
            text_y_start=resolved["text_y_start"], 
            cta_image_path=resolved["cta_path"],
            watermark_path=resolved["watermark_path"],
            music_base_path=resolved["music_base_path"],
            music_strategy=resolved["music_strategy"],
            modo_test=modo_test,
        )

        print(f"[PIPELINE V2] OK {i+1}/{quantity} → {output_path}")
