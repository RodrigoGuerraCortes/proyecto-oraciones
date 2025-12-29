# generator/v2/pipeline/short_pipeline.py

import uuid
import os

from generator.v2.content.selector_simple import elegir_texto_simple
from generator.v2.content.parser import parse_content
from generator.v2.video.short_renderer import render_short
from generator.v2.pipeline.config_resolver import resolve_short_config
from generator.v2.video.background_selector.with_history import HistoryBackgroundSelector
from generator.v2.content.title_resolver import resolve_title

from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import AudioRequest, TTSBlock
from generator.v2.audio.tts_engine import generate_voice

from generator.v2.content.layout.layout_resolver import resolve_layout


def run_short_pipeline(
    *,
    channel_config: dict,
    channel_id: int,
    format_code: str,
    quantity: int,
    modo_test: bool = False,
    force_text: str | None = None,
):
    """
    Pipeline genérico para SHORTS v2.
    """

    fmt = channel_config["formats"][format_code]
    content_path = fmt["content"]["path"]
    mode = fmt["content"]["type"]
    max_blocks = fmt["content"].get("max_blocks")

    output_dir = f"videos/test/{format_code}" if modo_test else f"videos/{format_code}"
    os.makedirs(output_dir, exist_ok=True)

    for _ in range(quantity):

        resolved = resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
        )

        audio_req = resolved["audio_req"]
        audio_cfg = fmt["audio"]["tts"]
        tts_mode = audio_cfg.get("mode", "continuous")

        base_path = resolved["content_base_path"]

        # -----------------------------------
        # Selección de texto
        # -----------------------------------
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

        parsed = parse_content(
            raw_text=raw_text,
            title=title,
            mode=mode,
            max_blocks=max_blocks,
        )

        # =================================================
        # TTS MODE: BLOCKS (ej: salmos)
        # =================================================
        if audio_req.tts_enabled and tts_mode == "blocks":

            tts_blocks: list[TTSBlock] = []
            current_t = 0.0

            pause_after_title = float(audio_cfg.get("pause_after_title", 0.0))
            pause_between = float(audio_cfg.get("pause_between_blocks", 0.0))

            tts_dir = "tmp/tts"
            os.makedirs(tts_dir, exist_ok=True)

            # Título hablado (opcional)
            if pause_after_title > 0:
                path = f"{tts_dir}/{uuid.uuid4().hex}.wav"
                voz = generate_voice(title, path)
                dur = voz.duration + pause_after_title

                tts_blocks.append(
                    TTSBlock(text=title, start=current_t, duration=dur)
                )
                current_t += dur

            # Estrofas
            for block in parsed.blocks:
                path = f"{tts_dir}/{uuid.uuid4().hex}.wav"
                voz = generate_voice(block.text, path)
                dur = voz.duration + pause_between

                tts_blocks.append(
                    TTSBlock(text=block.text, start=current_t, duration=dur)
                )
                current_t += dur

            audio_req.tts_blocks = tts_blocks
            audio_req.tts_text = None

            cta_dur = resolved["render_cfg"].cta_seconds if resolved["cta_path"] else 0.0
            audio_req.duration = current_t + cta_dur

            fmt["content"]["_tts_enabled"] = True
            fmt["content"]["_tts_mode"] = "blocks"
            fmt["content"].pop("seconds_per_block", None)

        # =================================================
        # TTS MODE: CONTINUOUS (ej: oraciones)
        # =================================================
        elif audio_req.tts_enabled and tts_mode == "continuous":

            full_text = "\n\n".join(b.text for b in parsed.blocks)
            audio_req.tts_text = full_text
            audio_req.tts_blocks = None

            preview = AudioRequest(
                duration=999.0,
                tts_enabled=True,
                tts_text=full_text,
                music_enabled=False,
            )

            audio_preview = build_audio(preview)
            fmt["content"]["_tts_duration"] = audio_preview.tts_duration
            fmt["content"]["_tts_enabled"] = True

        else:
            audio_req.tts_enabled = False
            audio_req.tts_text = None
            audio_req.tts_blocks = None

        # -----------------------------------
        # Layout
        # -----------------------------------
        visual_blocks = resolve_layout(
            parsed=parsed,
            content_cfg=fmt["content"],
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
        render_short(
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

        print(f"[PIPELINE V2] OK → {output_path}")
