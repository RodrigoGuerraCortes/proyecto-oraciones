from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    VideoFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
)
from moviepy.audio.fx.all import audio_loop, volumex

import os
import json
import math
from glob import glob

from generator.v3.adapter.persistir_adapter import persistir_video_v3
from generator.v3.tractor.fase_1_5_tts_layers import generar_tts_layers

# -------------------------------------------------
# Configuración de chunking
# -------------------------------------------------
CHUNK_SIZE = 25
TMP_CHUNKS_DIR = "/mnt/storage/tmp/chunks"

# -------------------------------------------------
# Utilidad: encontrar audio por base name
# -------------------------------------------------
def find_audio(base_name, audio_path):
    for ext in (".wav", ".mp3"):
        p = os.path.join(audio_path, base_name + ext)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"Audio faltante para layer {base_name} (.wav/.mp3)"
    )


# -------------------------------------------------
# Render de un chunk individual
# -------------------------------------------------
def render_chunk(
    *,
    chunk_index: int,
    layers: list,
    output_path: str,
    width: int,
    height: int,
    fps: int,
):
    print(f"[CHUNK {chunk_index}] Renderizando {len(layers)} layers")
    base_start = layers[0]["start"]

    clips = []
    #audio_clips = []



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
        audio_path = layer.get("audio")
        if audio_path and os.path.exists(audio_path):
            a = AudioFileClip(audio_path)
            a = a.subclip(0, min(a.duration, layer["duration"]))
            a = a.set_start(layer["start"] - base_start)
            a = a.audio_fadeout(0.15)
            clip = clip.set_audio(a)


        clips.append(clip)


    duration = layers[-1]["end"] - base_start

    background = (
        ImageClip(layers[0]["background"])
        .resize((width, height))
        .set_duration(duration)
    )


    video = CompositeVideoClip(
        [background] + clips,
        size=(width, height)
    ).set_duration(duration)

   

    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio=True,
        preset="ultrafast",
        threads=4,
        audio_codec="aac",
        audio_bitrate="192k",
    )

    # Liberar memoria explícitamente
    video.close()
    background.close()
    for c in clips:
        c.close()


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
    music_path: str = None,
    **kwargs,
):
    print("[LONG TRACTOR] FASE 2 — COMPOSITOR AUDIO-SYNC (CHUNKED)")
    print("[LONG TRACTOR] Modo test:", modo_test)


    print("[LONG TRACTOR] Music path:", music_path)


    #if not modo_test:
    #    raise RuntimeError("FASE 2 solo permitida en modo test")

    WIDTH = 1280 if modo_test else 1920
    HEIGHT = 720 if modo_test else 1080
    FPS = 15
    FADE_SECONDS = 0.4
    AUDIO_PADDING = 1.0 # segundos extra por layer

    content_cfg = resolved_config["content"]
    visual_cfg = resolved_config["visual"]
    audio_cfg = resolved_config["audio"]

    layers_path = content_cfg["layers_path"]
    background_path_test = visual_cfg["background_test"]
    background_path = visual_cfg["base_path"]

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
    chunk_files = []

    images = sorted(
        glob(os.path.join(background_path, "img_*.png"))
    )
    if not images:
        raise RuntimeError("No se encontraron imágenes de background")

    # Modo test: solo 4 imágenes
    if modo_test:
        images = images[:4]


    timeline = []
    current_time = 0.0
    IMAGE_INTERVAL = 450 if modo_test else 180

    for base_name in sequence:
        png = os.path.join(layers_path, base_name + ".png")
        audio_file = find_audio(base_name, audio_path)

        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio faltante: {audio_file}")

        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration + AUDIO_PADDING

        bg_index = int(current_time // IMAGE_INTERVAL) % len(images)
        bg_image = images[bg_index]
        print(
            f"[TIMELINE] t={current_time:6.1f}s | "
            f"bg_index={bg_index} | "
            f"bg={os.path.basename(bg_image)} | "
            f"layer={base_name}"
        )

        timeline.append({
            "image": png,
            "background": bg_image,
            "audio": audio_file,
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
    MAX_TEST_SECONDS = 900 if modo_test else None  # 2 minutos

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

    for idx, chunk_layers in enumerate(chunks, start=1):

        print(
            f"[CHUNK {idx}] "
            f"layers={len(chunk_layers)} | "
            f"bg={os.path.basename(chunk_layers[0]['background'])}"
        )
        chunk_out = os.path.join(
            TMP_CHUNKS_DIR,
            f"chunk_{idx:03d}.mp4"
        )

        render_chunk(
            chunk_index=idx,
            layers=chunk_layers,
            #background_path=background_path_test if modo_test else background_path,
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
    final_audio = final.audio

    if music_path and os.path.exists(music_path):
        print("[FASE 2] Integrando música de fondo")

        music = AudioFileClip(music_path)

        # 🔑 Saltar los primeros 15 segundos (silencio / intro)
        music = music.subclip(15)

        # Loop para cubrir todo el video
        music = audio_loop(music, duration=final.duration)

        # Volumen MUY bajo (clave)
        music = volumex(music, 0.17)  # 17% aprox

        # Fade suave
        music = music.audio_fadein(3.0).audio_fadeout(6.0)

        # Mezclar música + voz existente
        final_audio = CompositeAudioClip([
            final.audio,
            music
        ])

    final = final.set_audio(final_audio)

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
