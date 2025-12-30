# generator/v2/pipeline/short/plain.py

import os
import random
import uuid

from generator.v2.content.selector_simple import elegir_texto_simple
from generator.v2.content.parser import parse_content
from generator.v2.content.title_resolver import resolve_title
from generator.v2.content.layout.layout_resolver import resolve_layout

from generator.v2.pipeline.config_resolver import resolve_short_config
from generator.v2.video.background_selector.with_history import HistoryBackgroundSelector
from generator.v2.video.short.plain_renderer import render_short_plain

from generator.v2.pipeline.audio.tts_preparer import prepare_tts_if_needed


def run_short_plain(
    *,
    channel_config: dict,
    channel_id: int,
    format_code: str,
    quantity: int,
    modo_test: bool = False,
    force_text: str | None = None,
):
    """
    Pipeline SHORT – modo PLAIN (Ej: oraciones continuas)
    """

    fmt = channel_config["formats"][format_code]
    content_cfg = fmt["content"]
    content_path = content_cfg["path"]

    output_dir = f"videos/test/{format_code}" if modo_test else f"videos/{format_code}"
    os.makedirs(output_dir, exist_ok=True)

    for _ in range(quantity):

        # -----------------------------------
        # Config base
        # -----------------------------------
        resolved = resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
        )

        audio_req = resolved["audio_req"]

        # -----------------------------------
        # Texto
        # -----------------------------------
        base_path = resolved["content_base_path"]

        if force_text:
            path_txt = (
                force_text
                if os.path.isabs(force_text)
                else os.path.join(base_path, content_path, force_text)
            )
            base_name = os.path.splitext(os.path.basename(path_txt))[0]
        else:
            path_txt, base_name = elegir_texto_simple(
                base_path=base_path,
                sub_path=content_path,
            )

        with open(path_txt, "r", encoding="utf-8") as f:
            raw_text = f.read()

        title = resolve_title(
            parsed_title=base_name.replace("_", " ").strip(),
            path_txt=path_txt,
        )

        # -----------------------------------
        # Parseo (PLAIN)
        # -----------------------------------
        parsed = parse_content(
            raw_text=raw_text,
            title=title,
            mode="plain",
        )

        # -----------------------------------
        # Regla editorial TTS (PRE-LAYOUT)
        # -----------------------------------
        blocks_count = len(parsed.blocks)

        if blocks_count > 1:
            audio_req.tts_enabled = True
            print("[EDITORIAL] TTS FORZADO (multi-bloque)")
        else:
            if random.random() < audio_req.tts_ratio:
                audio_req.tts_enabled = True
                print("[EDITORIAL] TTS habilitado por ratio")
            else:
                audio_req.tts_enabled = False
                print("[EDITORIAL] TTS omitido por ratio")

        # -----------------------------------
        # Preparar TTS (preview real, PRE-LAYOUT)
        # -----------------------------------
        prepare_tts_if_needed(
            audio_req=audio_req,
            parsed_blocks=parsed.blocks,
            content_cfg=content_cfg,
        )

        # -----------------------------------
        # Layout visual (ya adaptado al TTS)
        # -----------------------------------
        visual_blocks = resolve_layout(
            parsed=parsed,
            content_cfg=content_cfg,
            text_style=resolved["text_style"],
        )

        # -----------------------------------
        # Background
        # -----------------------------------
        bg_selector = HistoryBackgroundSelector(
            base_path=resolved["background_selector_cfg"]["base_path"],
            ventana=resolved["background_selector_cfg"]["ventana"],
            fallback=resolved["background_selector_cfg"]["fallback"],
        )

        image_path = bg_selector.elegir(
            text=raw_text,
            title=title,
            format_code=format_code,
            channel_id=channel_id,
        )

        output_path = f"{output_dir}/{uuid.uuid4().hex[:8]}__{base_name}.mp4"

        # -----------------------------------
        # Render
        # -----------------------------------
        render_short_plain(
            title=title,
            blocks=visual_blocks,
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
            modo_test=modo_test,
        )

        print(f"[PIPELINE][PLAIN] OK → {output_path}")
