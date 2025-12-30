# generator/v2/pipeline/short/stanza.py

import os
import uuid

from generator.v2.content.selector_simple import elegir_texto_simple
from generator.v2.content.parser import parse_content
from generator.v2.content.title_resolver import resolve_title
from generator.v2.content.layout.layout_resolver import resolve_layout

from generator.v2.pipeline.config_resolver import resolve_short_config
from generator.v2.video.background_selector.with_history import HistoryBackgroundSelector
from generator.v2.video.short.stanza_renderer import render_short_stanza

from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import AudioRequest, TTSBlock


# Defaults “litúrgicos” (si no vienen en config)
DEFAULT_PAUSE_BETWEEN_BLOCKS = 1.2
DEFAULT_PAUSE_AFTER_TITLE = 1.0


def run_short_stanza(
    *,
    channel_config: dict,
    channel_id: int,
    format_code: str,
    quantity: int,
    modo_test: bool = False,
    force_text: str | None = None,
):
    """
    Pipeline SHORT – modo STANZAS (Ej: salmos por estrofa)

    Responsabilidad del pipeline:
    - parsear contenido (estrofas)
    - construir layout visual base
    - si TTS mode == "blocks": medir duración real de voz por estrofa y armar tts_blocks
    - ajustar DURACIONES visuales para que acompañen el audio (autoridad del audio)
    - renderer NO decide TTS
    """

    fmt = channel_config["formats"][format_code]
    content_cfg = fmt["content"]
    content_path = content_cfg["path"]

    tts_cfg = fmt.get("audio", {}).get("tts", {}) or {}
    tts_mode = tts_cfg.get("mode", "continuous")  # "blocks" en salmos
    pause_between = float(tts_cfg.get("pause_between_blocks", DEFAULT_PAUSE_BETWEEN_BLOCKS))
    pause_after_title = float(tts_cfg.get("pause_after_title", DEFAULT_PAUSE_AFTER_TITLE))

    # Opcional: si algún día quieres “título hablado”, lo habilitas por config
    # (por defecto False para mantenerlo simple y consistente visualmente)
    speak_title = bool(tts_cfg.get("speak_title", False))

    output_dir = f"videos/test/{format_code}" if modo_test else f"videos/{format_code}"
    os.makedirs(output_dir, exist_ok=True)

    for _ in range(quantity):
        # -----------------------------------
        # 1) Config base
        # -----------------------------------
        resolved = resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
        )

        audio_req = resolved["audio_req"]

        # -----------------------------------
        # 2) Selección de texto
        # -----------------------------------
        base_path = resolved["content_base_path"]

        if force_text:
            path_txt = (
                force_text
                if os.path.isabs(force_text)
                else os.path.join(base_path, content_path, force_text)
            )
            if not os.path.exists(path_txt):
                raise FileNotFoundError(f"Archivo de texto no existe: {path_txt}")

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
        # 3) Parseo (STANZAS)
        # -----------------------------------
        parsed = parse_content(
            raw_text=raw_text,
            title=title,
            mode="stanzas",
            max_blocks=content_cfg.get("max_blocks"),
        )

        # -----------------------------------
        # 4) Layout base (duraciones “editoriales” si NO hay TTS blocks)
        # -----------------------------------
        visual_blocks = resolve_layout(
            parsed=parsed,
            content_cfg=content_cfg,
            text_style=resolved["text_style"],
        )

        if not visual_blocks:
            raise RuntimeError("No se generaron bloques visuales")

        # -----------------------------------
        # 5) TTS por BLOQUES (salmos)
        # -----------------------------------
        # Nota: aquí NO hardcodeamos “salmo/oración”.
        # Es una estrategia por CONFIG (tts.mode == blocks).
        if audio_req.tts_enabled and tts_mode == "blocks":
            # Construimos TTSBlocks con duración REAL (voz + pausas)
            tts_blocks: list[TTSBlock] = []
            current_t = 0.0

            # (Opcional) Título hablado
            if speak_title:
                preview_title = AudioRequest(
                    duration=999.0,
                    tts_enabled=True,
                    tts_text=title,
                    tts_blocks=None,
                    music_enabled=False,
                )
                title_preview = build_audio(preview_title)
                title_voice_dur = float(title_preview.tts_duration or 0.0)
                title_block_dur = title_voice_dur + pause_after_title

                tts_blocks.append(
                    TTSBlock(
                        text=title,
                        start=current_t,
                        duration=title_block_dur,
                    )
                )
                current_t += title_block_dur

            # Estrofas habladas
            # Medimos cada estrofa con preview sin música (rápido, no contamina la mezcla)
            # y seteamos duración = voz + pause_between
            new_visual_durations: list[float] = []

            for vb in visual_blocks:
                stanza_text = vb["text"]

                preview_req = AudioRequest(
                    duration=999.0,
                    tts_enabled=True,
                    tts_text=stanza_text,
                    tts_blocks=None,
                    music_enabled=False,
                )
                prev_audio = build_audio(preview_req)
                voice_dur = float(prev_audio.tts_duration or 0.0)

                block_dur = voice_dur + pause_between

                tts_blocks.append(
                    TTSBlock(
                        text=stanza_text,
                        start=current_t,
                        duration=block_dur,
                    )
                )
                current_t += block_dur
                new_visual_durations.append(block_dur)

            # Ajuste 1: la mezcla final debe durar TODO el segmento hablado (más CTA abajo)
            audio_req.tts_blocks = tts_blocks
            audio_req.tts_text = None  # importante: blocks manda
            audio_req.duration = current_t  # CTA se suma en el renderer

            # Ajuste 2: el visual debe acompañar el audio (mismas duraciones por estrofa)
            for idx, dur in enumerate(new_visual_durations):
                visual_blocks[idx]["duration"] = dur

            # “Hint” para layout/diagnóstico
            content_cfg["_tts_enabled"] = True
            content_cfg["_tts_mode"] = "blocks"
        else:
            # No blocks: se puede usar seconds_per_block o lo que defina layout_stanzas
            audio_req.tts_blocks = None
            content_cfg["_tts_mode"] = "continuous" if audio_req.tts_enabled else "off"

            # Para modo no-blocks, si hay TTS (poco usual en salmos), lo más seguro es
            # setear texto completo y que sea continuo.
            if audio_req.tts_enabled:
                full_text = "\n\n".join(b.text for b in parsed.blocks)
                audio_req.tts_text = full_text
                content_cfg["_tts_enabled"] = True
            else:
                audio_req.tts_text = None
                content_cfg["_tts_enabled"] = False

        # Modo test: conserva música, pero desactiva TTS para comparación visual
        if modo_test:
            audio_req.tts_enabled = False
            audio_req.tts_blocks = None
            audio_req.tts_text = None

        # -----------------------------------
        # 6) Background
        # -----------------------------------
        bg_selector = HistoryBackgroundSelector(
            base_path=resolved["background_selector_cfg"]["base_path"],
            ventana=resolved["background_selector_cfg"]["ventana"],
            fallback=resolved["background_selector_cfg"]["fallback"],
        )

        full_text_for_bg = "\n\n".join(b.text for b in parsed.blocks)
        image_path = bg_selector.elegir(
            text=full_text_for_bg,
            title=title,
            format_code=format_code,
            channel_id=channel_id,
        )

        # -----------------------------------
        # 7) Output
        # -----------------------------------
        output_path = f"{output_dir}/{uuid.uuid4().hex[:8]}__{base_name}.mp4"

        # -----------------------------------
        # 8) Render
        # -----------------------------------
        render_short_stanza(
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

        print(f"[PIPELINE][STANZA] OK → {output_path}")
