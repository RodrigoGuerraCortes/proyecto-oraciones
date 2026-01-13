from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
)
import os
import json
from glob import glob
import sys
from moviepy.audio.AudioClip import AudioClip
import numpy as np

from adapter.persistir_adapter import persistir_video_v3

# -------------------------------------------------
# Configuración
# -------------------------------------------------
TMP_CHUNKS_DIR = "/mnt/storage/tmp/chunks"

# Debug flags
DEBUG = True
DEBUG_TIMELINE_PREVIEW_N = 6        # cuántos eventos imprimir al inicio
DEBUG_CHUNK_PREVIEW_N = 2          # cuántos layers imprimir por chunk
DEBUG_OVERLAP_EPS = 0.02             # tolerancia segundos para "no overlap"

# Test controls
TEST_MAX_SECONDS = 120             # en modo_test, corta timeline en 500s
TEST_SILENCE_SECONDS = 10.0          # en modo_test, fuerza silencios a 50s


# -------------------------------------------------
# Utilidad: encontrar audio por base name
# -------------------------------------------------
def find_audio(base_name, audio_path):
    for ext in (".wav", ".mp3"):
        p = os.path.join(audio_path, base_name + ext)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"Audio faltante para layer {base_name} (.wav/.mp3)")


def slow_zoom_bg(img_path, duration, width, height, zoom_to=1.02):
    base = ImageClip(img_path).resize((width, height))
    return (
        base.resize(lambda t: 1 + (zoom_to - 1) * (t / max(duration, 0.001)))
        .set_duration(duration)
    )


# -------------------------------------------------
# Debug: helpers
# -------------------------------------------------
def _basename_noext(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def debug_print_timeline(timeline, title="[TIMELINE]"):
    if not DEBUG:
        return

    print(f"{title} total_events={len(timeline)}")
    for i, ev in enumerate(timeline[:DEBUG_TIMELINE_PREVIEW_N]):
        kind = ev.get("kind")
        start = ev.get("start")
        end = ev.get("end")
        dur = ev.get("duration")
        bg = _basename_noext(ev.get("background", "")) if ev.get("background") else "-"
        img = _basename_noext(ev.get("image", "")) if ev.get("image") else "-"
        aud = _basename_noext(ev.get("audio", "")) if ev.get("audio") else "-"
        print(
            f"  #{i:03d} kind={kind:<7} start={start:8.2f} end={end:8.2f} dur={dur:6.2f} "
            f"bg={bg} img={img} aud={aud}"
        )


def validate_timeline(timeline):
    """
    Valida:
      - start/end coherentes
      - no solapes (con tolerancia)
      - monotonicidad
    """
    if not DEBUG:
        return

    print("[TIMELINE][VALIDATE] Iniciando validación…")

    prev_end = None
    issues = 0

    for i, ev in enumerate(timeline):
        s = float(ev["start"])
        e = float(ev["end"])
        d = float(ev["duration"])

        if e < s - DEBUG_OVERLAP_EPS:
            issues += 1
            print(f"[TIMELINE][ERROR] Event #{i} end < start: start={s} end={e}")

        if abs((e - s) - d) > 0.15:
            # tolerancia por rounding/codec; si esto explota, hay bug de duraciones
            issues += 1
            print(
                f"[TIMELINE][WARN] Event #{i} (end-start) != duration: "
                f"(end-start)={(e-s):.3f} duration={d:.3f}"
            )

        if prev_end is not None:
            if s < prev_end - DEBUG_OVERLAP_EPS:
                issues += 1
                print(
                    f"[TIMELINE][OVERLAP] Event #{i} starts before prev_end: "
                    f"start={s:.3f} prev_end={prev_end:.3f} delta={(s-prev_end):.3f} kind={ev.get('kind')}"
                )
        prev_end = e

    if issues == 0:
        print("[TIMELINE][VALIDATE] OK — sin solapes ni inconsistencias relevantes.")
    else:
        print(f"[TIMELINE][VALIDATE] Encontrados issues={issues} (revisar logs arriba).")


def trim_timeline_by_end(timeline, max_seconds):
    """
    Corta timeline por tiempo global: mantiene eventos cuya start < max_seconds,
    y recorta el último si su end excede el límite.
    """
    if max_seconds is None:
        return timeline

    out = []
    for ev in timeline:
        if ev["start"] >= max_seconds:
            break

        ev2 = dict(ev)
        if ev2["end"] > max_seconds:
            ev2["end"] = float(max_seconds)
            ev2["duration"] = ev2["end"] - ev2["start"]
        out.append(ev2)

    return out


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
    intro_seconds: float = 0.0,
    watermark_cfg: dict | None = None,
):
    print(f"[CHUNK {chunk_index}] Renderizando events={len(layers)} → {output_path}")

    # --- inicio real del chunk (incluye intro) ---
    first_start = min(l["start"] for l in layers)
    chunk_start = first_start - max(0.0, float(intro_seconds))
    if chunk_start < 0:
        chunk_start = 0.0

    first_rel = first_start - chunk_start

    print(
        f"[CHUNK {chunk_index}] first_start={first_start:.2f} | "
        f"chunk_start={chunk_start:.2f} | first_rel={first_rel:.2f} | "
        f"intro={intro_seconds:.2f}"
    )

    # --- debug preview del chunk ---
    if DEBUG:
        print(f"[CHUNK {chunk_index}][PREVIEW] (primeros {min(DEBUG_CHUNK_PREVIEW_N, len(layers))} eventos)")
        for i, ev in enumerate(layers[:DEBUG_CHUNK_PREVIEW_N]):
            kind = ev.get("kind")
            rel_s = ev["start"] - chunk_start
            rel_e = ev["end"] - chunk_start
            bg = _basename_noext(ev.get("background", "")) if ev.get("background") else "-"
            img = _basename_noext(ev.get("image", "")) if ev.get("image") else "-"
            aud = _basename_noext(ev.get("audio", "")) if ev.get("audio") else "-"
            print(
                f"  ev#{i:03d} kind={kind:<7} rel_start={rel_s:7.2f} rel_end={rel_e:7.2f} "
                f"dur={ev.get('duration',0):6.2f} bg={bg} img={img} aud={aud}"
            )

    # --- construir clips ---
    clips = []
    image_cache = {}

    for ev in layers:
        kind = ev.get("kind")
        rel_start = ev["start"] - chunk_start
        duration = ev["duration"]

        if kind == "silence":
            # IMPORTANTE: start debe ser RELATIVO, no global
            # Este clip sólo asegura "hold" visual (sin audio).
            hold = (
                ImageClip(ev["background"])
                .resize((width, height))
                .set_start(rel_start)
                .set_duration(duration)
            )

            #Se agrega audio silencioso para evitar problemas de audio en el video final
            silent = silent_audio(duration).set_start(rel_start)
            hold = hold.set_audio(silent)

            clips.append(hold)
            continue

        # kind == layer
        img_path = ev["image"]
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            raise RuntimeError(f"Imagen inválida o vacía: {img_path}")

        if img_path not in image_cache:
            image_cache[img_path] = ImageClip(img_path).resize((width, height))

        clip = (
            image_cache[img_path]
            .set_start(rel_start)
            .set_duration(duration)
            .fadein(ev["fade"])
            .fadeout(ev["fade"])
        )

        audio_path = ev.get("audio")
        if audio_path and os.path.exists(audio_path):
            a = AudioFileClip(audio_path)
            # asegura no pedir más de lo que dura
            a = a.subclip(0, min(a.duration, duration))
            a = a.set_start(rel_start)
            a = a.audio_fadeout(0.15)
            clip = clip.set_audio(a)

        clips.append(clip)

    # --- duración del chunk incluye intro ---
    duration = max(l["end"] for l in layers) - chunk_start
    if duration <= 0:
        raise RuntimeError(f"[CHUNK {chunk_index}] Duración inválida: {duration}")

    # --- backgrounds: debe existir desde t=0 ---
    bg_clips = []
    first_bg = layers[0]["background"]

    # tramo inicial (intro) desde 0 hasta first_rel
    if first_rel > 0:
        bg_clips.append(
            slow_zoom_bg(first_bg, duration=first_rel, width=width, height=height, zoom_to=1.02)
            .set_start(0)
            .fadein(min(2.5, first_rel))
        )

    # cambios de background según eventos
    last_bg = None
    last_start = None

    for ev in layers:
        bg = ev["background"]
        if bg != last_bg:
            if last_bg is not None:
                bg_clips.append(
                    ImageClip(last_bg)
                    .resize((width, height))
                    .set_start(last_start - chunk_start)
                    .set_duration(ev["start"] - last_start)
                )
            last_bg = bg
            last_start = ev["start"]

    # último tramo
    bg_clips.append(
        ImageClip(last_bg)
        .resize((width, height))
        .set_start(last_start - chunk_start)
        .set_duration(max(l["end"] for l in layers) - last_start)
    )

    video = CompositeVideoClip(bg_clips + clips, size=(width, height)).set_duration(duration)

    # -------------------------------------------------
    # WATERMARK (si está configurado)
    # -------------------------------------------------
    if watermark_cfg:
        print(
            f"[CHUNK {chunk_index}] Aplicando watermark:",
            watermark_cfg
        )
        video = aplicar_watermark(
            video,
            watermark_cfg,
            width,
            height,
        )

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

    # cleanup
    video.close()
    for c in clips:
        try:
            c.close()
        except Exception:
            pass

    print(f"[CHUNK {chunk_index}] OK")


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

    WIDTH = 1280 if modo_test else 1920
    HEIGHT = 720 if modo_test else 1080
    FPS = 15
    FADE_SECONDS = 0.4
    INTER_LAYER_GAP_SECONDS = 2.2 #Esto depende del tractor ... tiempo de respiración entre layers
    # Offsets
    TTS_OFFSET = 5.0
    GLOBAL_VISUAL_OFFSET = TTS_OFFSET

    content_cfg = resolved_config["content"]
    visual_cfg = resolved_config["visual"]
    audio_cfg = resolved_config["audio"]

    layers_path = content_cfg["layers_path"]
    background_path = visual_cfg["base_path"]
    audio_path = audio_cfg["audio_layers_path"]
    sequence_path = resolved_config.get("sequence_path")


    watermark_cfg = visual_cfg.get("watermark")
    if watermark_cfg:
        print("[LONG TRACTOR] Watermark cfg:", watermark_cfg) 


    os.makedirs(TMP_CHUNKS_DIR, exist_ok=True)

    # -------------------------------------------------
    # Cargar secuencia
    # -------------------------------------------------
    with open(os.path.join(sequence_path, "sequence.json"), "r", encoding="utf-8") as f:
        sequence_data = json.load(f)

    sequence = sequence_data["sequence"]
    print("[FASE 2] Usando sequence.json | items:", len(sequence))

    # -------------------------------------------------
    # Cargar pool de backgrounds
    # -------------------------------------------------
    images = sorted(glob(os.path.join(background_path, "img_*.png")))
    if not images:
        raise RuntimeError("No se encontraron imágenes de background")

    if modo_test:
        images = images[:4]


    # -------------------------------------------------
    # Estimar duración total para distribuir backgrounds (tarde → noche)
    # -------------------------------------------------
    estimated_total = float(GLOBAL_VISUAL_OFFSET)

    for item in sequence:
        if isinstance(item, str):
            audio_file = find_audio(item, audio_path)
            ac = AudioFileClip(audio_file)
            estimated_total += float(ac.duration)
            ac.close()
        elif isinstance(item, dict) and item.get("type") == "silence":
            d = float(item["duration_seconds"])
            if modo_test:
                d = min(d, TEST_SILENCE_SECONDS)
            estimated_total += d
        else:
            raise RuntimeError(f"Item inválido en sequence (estimate): {item}")

    scene_duration = estimated_total / len(images)
    print(f"[VISUAL] estimated_total={estimated_total:.2f}s | images={len(images)} | scene_duration={scene_duration:.2f}s")


    # -------------------------------------------------
    # Construcción de timeline
    # -------------------------------------------------
    timeline = []
    current_time = GLOBAL_VISUAL_OFFSET
    visual_offset_applied = False
    for idx, item in enumerate(sequence):
        # background para ESTE evento se calcula por current_time (antes de avanzar)
        bg_image = get_background_for_time(current_time, images, scene_duration)

        start = current_time

        if isinstance(item, str):
            base_name = item
            png = os.path.join(layers_path, base_name + ".png")
            audio_file = find_audio(base_name, audio_path)

            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"Audio faltante: {audio_file}")

            # Duración real del audio (sin padding temporal)
            audio_clip = AudioFileClip(audio_file)
            duration = float(audio_clip.duration)
            audio_clip.close()

            end = start + duration

            timeline.append({
                "kind": "layer",
                "seq_idx": idx,
                "name": base_name,
                "image": png,
                "background": bg_image,
                "audio": audio_file,
                "start": float(start),
                "duration": float(duration),
                "end": float(end),
                "fade": FADE_SECONDS,
            })

            current_time += duration

            # -------------------------------------------------
            # GAP contemplativo entre layers (respiración)
            # -------------------------------------------------
            if INTER_LAYER_GAP_SECONDS > 0:
                gap_start = current_time
                gap_end = gap_start + INTER_LAYER_GAP_SECONDS

                timeline.append({
                    "kind": "silence",
                    "seq_idx": idx,
                    "name": "inter_layer_gap",
                    "background": bg_image,
                    "start": float(gap_start),
                    "duration": float(INTER_LAYER_GAP_SECONDS),
                    "end": float(gap_end),
                    "audio": None,
                })

                current_time = gap_end

        elif isinstance(item, dict) and item.get("type") == "silence":
            silence_duration = float(item["duration_seconds"])
            if modo_test:
                silence_duration = min(silence_duration, TEST_SILENCE_SECONDS)

            end = start + silence_duration

            timeline.append({
                "kind": "silence",
                "seq_idx": idx,
                "name": "silence",
                "background": bg_image,
                "start": float(start),
                "duration": float(silence_duration),
                "end": float(end),
                "audio": None,
            })

            current_time += silence_duration
        else:
            raise RuntimeError(f"Item inválido en sequence (idx={idx}): {item}")

    # Debug timeline
    debug_print_timeline(timeline, title="[FASE 2][TIMELINE]")
    validate_timeline(timeline)

    # -------------------------------------------------
    # Modo test: cortar timeline a 500s (por tiempo global)
    # -------------------------------------------------
    if modo_test:
        timeline = trim_timeline_by_end(timeline, TEST_MAX_SECONDS)
        print(f"[FASE 2][TEST] Timeline recortado a {TEST_MAX_SECONDS}s → events={len(timeline)}")
        validate_timeline(timeline)

    if not timeline:
        raise RuntimeError("Timeline vacío tras recortes.")

    total_end = timeline[-1]["end"]
    print("[FASE 2] Duración estimada:", round(total_end / 60, 2), "min")

    # -------------------------------------------------
    # Render por chunks
    # -------------------------------------------------
    MAX_CHUNK_SECONDS = 600  # 10 minutos
    chunks = []
    current_chunk = []
    chunk_start = timeline[0]["start"]

    for ev in timeline:
        if (ev["end"] - chunk_start) > MAX_CHUNK_SECONDS and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            chunk_start = ev["start"]
        current_chunk.append(ev)

    if current_chunk:
        chunks.append(current_chunk)

    print(f"[FASE 2] Chunks a renderizar: {len(chunks)}")

    chunk_files = []
    for cidx, chunk_layers in enumerate(chunks, start=1):
        chunk_out = os.path.join(TMP_CHUNKS_DIR, f"chunk_{cidx:03d}.mp4")

        print(
            f"[FASE 2] → CHUNK {cidx}: events={len(chunk_layers)} "
            f"start={chunk_layers[0]['start']:.2f} end={chunk_layers[-1]['end']:.2f} "
            f"bg={os.path.basename(chunk_layers[0]['background'])}"
        )

        render_chunk(
            chunk_index=cidx,
            layers=chunk_layers,
            output_path=chunk_out,
            width=WIDTH,
            height=HEIGHT,
            fps=FPS,
            intro_seconds=(TTS_OFFSET if cidx == 1 else 0.0),
            watermark_cfg=watermark_cfg,
        )

        chunk_files.append(chunk_out)

    print("[FASE 2] Chunks generados:", len(chunk_files))
    print("[FASE 2] Output final:", output_path)

    # -------------------------------------------------
    # Concatenación + música (idéntico a tu lógica)
    # -------------------------------------------------
    concat_list = os.path.join(TMP_CHUNKS_DIR, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in chunk_files:
            f.write(f"file '{os.path.abspath(p)}'\n")

    tmp_no_music = output_path.replace(".mp4", "_nomusic.mp4")

    cmd_concat = (
        f"ffmpeg -y "
        f"-f concat -safe 0 "
        f"-i {concat_list} "
        f"-c copy "
        f"{tmp_no_music}"
    )

    ret = os.system(cmd_concat)
    if ret != 0:
        raise RuntimeError("Error en concatenación ffmpeg")

    if music_path and os.path.exists(music_path):
        print("[FASE 2] Agregando música de fondo con ffmpeg")

        cmd_music = (
            f"ffmpeg -y "
            f"-i \"{tmp_no_music}\" "
            f"-i \"{music_path}\" "
            f"-filter_complex "
            f"\""
            f"[0:a]acompressor=threshold=-18dB:ratio=2:attack=20:release=250,volume=0.75[a_tts];"
            f"[1:a]aloop=loop=-1:size=2e+09,volume=0.35[a_music];"
            f"[a_tts][a_music]amix=inputs=2:weights=1 1:dropout_transition=6[aout]"
            f"\" "
            f"-map 0:v "
            f"-map \"[aout]\" "
            f"-c:v copy "
            f"-c:a aac "
            f"-shortest "
            f"\"{output_path}\""
        )

        ret = os.system(cmd_music)
        if ret != 0:
            raise RuntimeError("Error agregando música")
    else:
        os.rename(tmp_no_music, output_path)

    print("[FASE 2] Video final generado:", output_path)

    # Persistencia (tu lógica actual)
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo="long_tractor_oracion",
        output_path=output_path,
        texto="FASE 2 — Layers sincronizados por audio (chunked) DEBUG",
        imagen_usada=os.path.basename(background_path),
        musica_usada=None,
        fingerprint=None,
        usar_tts=False,
        modo_test=True,
        licencia_path=None,
    )

    print("[LONG TRACTOR] FASE 2 OK — Render chunked completado")


def aplicar_watermark(video, wm_cfg, width, height):
    wm = (
        ImageClip(wm_cfg["path"])
        .resize(wm_cfg.get("scale", 0.22))
        .set_duration(video.duration)
        .set_opacity(0.85)
    )

    margin = wm_cfg.get("margin", 12)

    wm = wm.set_position((
        width - wm.w - margin,
        height - wm.h - margin,
    ))

    return CompositeVideoClip([video, wm], size=(width, height))


def silent_audio(duration, fps=44100):
    return AudioClip(
        make_frame=lambda t: np.zeros((1,)),
        duration=duration,
        fps=fps
    )

def get_background_for_time(t: float, images: list[str], scene_duration: float) -> str:
    # Avanza monotónicamente: no usa módulo, no “recicla” imágenes.
    idx = int(t // max(scene_duration, 0.001))
    if idx < 0:
        idx = 0
    if idx >= len(images):
        idx = len(images) - 1
    return images[idx]