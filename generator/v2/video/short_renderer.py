# generator/v2/video/short_renderer.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import os

from moviepy.editor import ImageClip

from generator.v2.video.background_renderer import render_background
from generator.v2.video.title_renderer import render_title_layer, TitleStyle
from generator.v2.video.text_renderer import render_text_layer, TextStyle
from generator.v2.video.watermark_renderer import render_watermark_layer
from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import ComposerRequest
from generator.v2.video.cta_renderer import render_cta_clip

from generator.v2.audio.audio_builder import build_audio
from generator.v2.audio.models import TTSBlock

ANCHO = 1080
ALTO = 1920
FINAL_BLOCK_EXTRA_SECONDS = 0.0
VOICE_VISUAL_TAIL = 0.4
POST_TEXT_PAUSE_SECONDS = 0.8

@dataclass
class ShortRenderConfig:
    """
    Mantener este dataclass es parte del contrato del pipeline.
    """
    max_lines: int
    cta_seconds: int
    fade_seconds: float = 1.0
    enable_fade_between_blocks: bool = True


def render_short(
    *,
    title: str,
    blocks: list[dict],  # [{"text": str, "duration": float}, ...]
    output_path: str,
    image_path: str,
    audio_req,
    config: ShortRenderConfig,
    background_cfg,
    title_style: TitleStyle,
    text_style: TextStyle,
    text_y_start: int,
    cta_image_path: str | None = None,
    watermark_path: str | None = None,
    modo_test: bool = False,
):
    """
    Renderer V2 por capas PNG.
    Entrada: bloques visuales ya resueltos (layout listo).
    """

    print(
        f"[RENDER] start | output={os.path.basename(output_path)} | "
        f"modo_test={modo_test} | cta={bool(cta_image_path)}"
    )

    if not blocks:
        raise ValueError("render_short recibió blocks vacío")

    # -------------------------------------------------
    # 1) Directorios
    # -------------------------------------------------
    render_dir = Path(output_path).parent
    layers_dir = render_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # 2) TEXTO → clips secuenciales
    # -------------------------------------------------
    text_clips: List[ImageClip] = []
    current_t = 0.0
    tts_blocks: list[TTSBlock] = []

    for i, b in enumerate(blocks):
        text = b["text"]
        base_duration = float(b["duration"])

        text_png = (layers_dir / f"text_block_{i}.png").resolve()

        render_text_layer(
            lines=text.splitlines(),
            output_path=str(text_png),
            style=text_style,
            y_start=text_y_start,
        )

        if not text_png.exists():
            raise RuntimeError(f"[RENDER ERROR] text layer not created: {text_png}")

        duration = _adjust_duration_for_test(base_duration, modo_test)

        is_last_block = (i == len(blocks) - 1)
        if is_last_block:
            duration += FINAL_BLOCK_EXTRA_SECONDS
            if FINAL_BLOCK_EXTRA_SECONDS != 0.0:
                print(
                    f"[BLOCK {i}][FINAL-EXTEND] "
                    f"+{FINAL_BLOCK_EXTRA_SECONDS:.1f}s → {duration:.2f}s"
                )

        print(
            f"[BLOCK {i}] "
            f"lines={len(text.splitlines())} | "
            f"duration={duration:.2f}s"
        )

        tts_blocks.append(
            TTSBlock(
                text=text,
                start=current_t,
                duration=duration,
            )
        )

        clip = (
            ImageClip(str(text_png))
            .set_start(current_t)
            .set_duration(duration)
        )

        if config.enable_fade_between_blocks:
            fade = config.fade_seconds

            # Margen visual para que la voz termine la frase
            visual_tail = VOICE_VISUAL_TAIL if audio_req and audio_req.tts_enabled else 0.0

            clip = (
                ImageClip(str(text_png))
                .set_start(current_t)
                .set_duration(duration + visual_tail)
                .fadein(fade)
            )

            # aplicar fadeout SOLO sobre el final real del texto
            clip = clip.fadeout(fade)

        text_clips.append(clip)
        current_t += duration

    text_duration = current_t
    # Pausa corta antes del CTA (sin cortar música)
    text_duration += POST_TEXT_PAUSE_SECONDS
    cta_duration = float(config.cta_seconds) if cta_image_path else 0.0
    total_duration = text_duration  # CTA se concatena en composer


    if audio_req.tts_enabled:
        audio_duration = text_duration + cta_duration
    else:
        audio_duration = text_duration

    print(
        "[TIMING] "
        f"text={text_duration:.2f}s | "
        f"cta={cta_duration:.2f}s | "
        f"total={audio_duration:.2f}s"
    )

    # -------------------------------------------------
    # 2.5) AUDIO (música / TTS)
    # -------------------------------------------------
    audio_clip = None
    
    if audio_req:
        # ⚠️ IMPORTANTE:
        # Si el pipeline ya definió TTS por bloques,
        # el renderer NO debe tocar nada del TTS
        if audio_req.tts_blocks:
            pass
        else:
            audio_req.duration = audio_duration   # ← USAR lo calculado

        print(
            "[AUDIO] "
            f"music={audio_req.music_enabled} | "
            f"tts={audio_req.tts_enabled} | "
            f"duration={audio_req.duration:.2f}s"
        )

        audio_result = build_audio(audio_req)
        audio_clip = audio_result.audio_clip

    # -------------------------------------------------
    # 3) FONDO
    # -------------------------------------------------
    
    fondo, grad = render_background(
        image_path=image_path,
        duration=audio_duration,
        config=background_cfg,
    )

    layers: List[ImageClip] = [fondo, grad]

    # -------------------------------------------------
    # 4) TÍTULO
    # -------------------------------------------------
    title_png = (layers_dir / "title.png").resolve()

    render_title_layer(
        title=title,
        output_path=str(title_png),
        style=title_style,
    )

    if not title_png.exists():
        raise RuntimeError(f"[RENDER ERROR] title layer not created: {title_png}")

    layers.append(
        ImageClip(str(title_png))
        .set_duration(total_duration)
    )

    # -------------------------------------------------
    # 5) WATERMARK
    # -------------------------------------------------
    if watermark_path and os.path.exists(watermark_path):
        wm_png = (layers_dir / "watermark.png").resolve()

        render_watermark_layer(
            watermark_path=watermark_path,
            output_path=str(wm_png),
        )

        if not wm_png.exists():
            raise RuntimeError(f"[RENDER ERROR] watermark layer not created: {wm_png}")

        layers.append(
            ImageClip(str(wm_png))
            .set_duration(total_duration)
        )

    # -------------------------------------------------
    # 5.5) CTA layers (se concatenan en composer)
    # -------------------------------------------------
    cta_layers = None

    if cta_image_path:
        CTA_DURATION = config.cta_seconds

        fondo_cta, grad_cta = render_background(
            image_path=image_path,
            duration=CTA_DURATION,
            config=background_cfg,
        )

        cta_clip = render_cta_clip(
            cta_image_path=cta_image_path,
            duration=CTA_DURATION,
        )

        cta_layers = [fondo_cta, grad_cta]
        if cta_clip:
            cta_layers.append(cta_clip)

    # -------------------------------------------------
    # 6) COMPOSICIÓN FINAL
    # -------------------------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=layers + text_clips,
            overlays=[],
            audio=audio_clip,
            cta_layers=cta_layers,
            output_path=output_path,
        )
    )

    return {
        "output": output_path,
        "layers_dir": str(layers_dir),
    }


def _adjust_duration_for_test(duration: float, modo_test: bool) -> float:
    """
    Reduce duración solo en modo test para acelerar validaciones visuales.
    """
    if not modo_test:
        return duration

    return max(3.0, duration * 0.15)
