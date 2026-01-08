from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    VideoFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
)
import os
import json
import math

from generator.v3.adapter.persistir_adapter import persistir_video_v3
from generator.v3.tractor.fase_1_5_tts_layers import generar_tts_layers

# -------------------------------------------------
# Configuración de chunking
# -------------------------------------------------
CHUNK_SIZE = 25
TMP_CHUNKS_DIR = "/mnt/storage/tmp/chunks"


# -------------------------------------------------
# Render de un chunk individual
# -------------------------------------------------
def render_chunk(
    *,
    chunk_index: int,
    layers: list,
    background_path: str,
    output_path: str,
    width: int,
    height: int,
    fps: int,
):
    print(f"[CHUNK {chunk_index}] Renderizando {len(layers)} layers")
    base_start = layers[0]["start"]

    clips = []
    audio_clips = []

    for layer in layers:
        clip = (
            ImageClip(layer["image"])
            .resize((width, height))
            .set_start(layer["start"] - base_start)
            .set_duration(layer["duration"])
            .fadein(layer["fade"])
            .fadeout(layer["fade"])
        )

        # --- AUDIO TTS por layer ---
        wav_path = layer.get("wav")
        if wav_path and os.path.exists(wav_path):
            a = AudioFileClip(wav_path)
            # El audio dura aprox layer["duration"] - padding; igual lo recortamos
            a = a.subclip(0, min(a.duration, layer["duration"]))
            clip = clip.set_audio(a)


        clips.append(clip)

        if "audio" in layer:
            audio = (
                AudioFileClip(layer["audio"])
                .set_start(layer["start"] - base_start)
            )
            audio_clips.append(audio)


    duration = layers[-1]["end"] - base_start

    background = (
        ImageClip(background_path)
        .resize((width, height))
        .set_duration(duration)
    )

    final_audio = None
    if audio_clips:
        final_audio = CompositeAudioClip(audio_clips)

    video = CompositeVideoClip(
        [background] + clips,
        size=(width, height)
    ).set_duration(duration)

    if final_audio:
        video = video.set_audio(final_audio)

    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio=True,
        preset="ultrafast",
        threads=4,
    )

    # Liberar memoria explícitamente
    video.close()
    background.close()
    for c in clips:
        c.close()

    for a in audio_clips:
        a.close()

    print(f"[CHUNK {chunk_index}] OK → {output_path}")


# -------------------------------------------------
# FASE 2 — Composición sincronizada por AUDIO (chunked)
# -------------------------------------------------
def generar_long_tractor(
    *,
    resolved_config: dict,
    output_path: str,
    video_id: str,
    channel_id: int,
    modo_test: bool = False,
    **kwargs,
):
    print("[LONG TRACTOR] FASE 2 — COMPOSITOR AUDIO-SYNC (CHUNKED)")
    print("[LONG TRACTOR] Modo test:", modo_test)

    if not modo_test:
        raise RuntimeError("FASE 2 solo permitida en modo test")

    WIDTH = 1280 if modo_test else 1920
    HEIGHT = 720 if modo_test else 1080
    FPS = 15
    FADE_SECONDS = 0.4
    AUDIO_PADDING = 0.2

    content_cfg = resolved_config["content"]
    visual_cfg = resolved_config["visual"]
    audio_cfg = resolved_config["audio"]

    layers_path = content_cfg["layers_path"]
    background_path = visual_cfg["background_test"]
    audio_path = audio_cfg["audio_layers_path"]

    sequence_path = resolved_config.get(
        "sequence_path",
        "/mnt/storage/generated/tractor_build/sequence.json"
    )
  



    os.makedirs(TMP_CHUNKS_DIR, exist_ok=True)

    # -------------------------------------------------
    # Cargar secuencia
    # -------------------------------------------------
    with open(sequence_path, "r", encoding="utf-8") as f:
        sequence_data = json.load(f)

    sequence = sequence_data["sequence"]
    print("[FASE 2] Usando sequence.json")
    print("[FASE 2] Total layers:", len(sequence))

    # -------------------------------------------------
    # Construcción del timeline global
    # -------------------------------------------------
    timeline = []
    current_time = 0.0

    for base_name in sequence:
        png = os.path.join(layers_path, base_name + ".png")
        wav = os.path.join(audio_path, base_name + ".wav")

        if not os.path.exists(wav):
            raise FileNotFoundError(f"Audio faltante: {wav}")

        audio_clip = AudioFileClip(wav)
        duration = audio_clip.duration + AUDIO_PADDING

        timeline.append({
            "image": png,
            "audio": wav,
            "start": current_time,
            "duration": duration,
            "end": current_time + duration,
            "fade": FADE_SECONDS,
        })

        current_time += duration
        audio_clip.close()

    total_duration = current_time
    print("[FASE 2] Duración total:", round(total_duration / 60, 2), "min")

    # -------------------------------------------------
    # TEST corto (limitación de duración)
    # -------------------------------------------------
    MAX_TEST_SECONDS = 120 if modo_test else None  # 2 minutos

    if MAX_TEST_SECONDS:
        limited_timeline = []
        acc = 0.0
        for item in timeline:
            if acc >= MAX_TEST_SECONDS:
                break
            limited_timeline.append(item)
            acc += item["duration"]

        timeline = limited_timeline
        print(
            "[FASE 2] Modo test corto:",
            round(acc, 2),
            "seg"
        )

    # -------------------------------------------------
    # Render por chunks
    # -------------------------------------------------
    chunks = [
        timeline[i:i + CHUNK_SIZE]
        for i in range(0, len(timeline), CHUNK_SIZE)
    ]

    chunk_files = []

    for idx, chunk_layers in enumerate(chunks, start=1):
        chunk_out = os.path.join(
            TMP_CHUNKS_DIR,
            f"chunk_{idx:03d}.mp4"
        )

        render_chunk(
            chunk_index=idx,
            layers=chunk_layers,
            background_path=background_path,
            output_path=chunk_out,
            width=WIDTH,
            height=HEIGHT,
            fps=FPS,
        )

        chunk_files.append(chunk_out)

    # -------------------------------------------------
    # Concatenación final
    # -------------------------------------------------
    print("[FASE 2] Concatenando chunks…")

    videos = [VideoFileClip(p) for p in chunk_files]

    final = concatenate_videoclips(
        videos,
        method="compose"
    )

    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=True,
        preset="ultrafast" if FPS <= 15 else "veryfast",
        threads = 2 if modo_test else 4,
    )

    for v in videos:
        v.close()

    final.close()

    # -------------------------------------------------
    # Persistencia mínima (modo test)
    # -------------------------------------------------
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo="long_tractor_oracion",
        output_path=output_path,
        texto="FASE 2 — Layers sincronizados por audio (chunked)",
        imagen_usada=os.path.basename(background_path),
        musica_usada=None,
        fingerprint=None,
        usar_tts=False,
        modo_test=True,
        licencia_path=None,
    )

    print("[LONG TRACTOR] FASE 2 OK — Render chunked completado")
