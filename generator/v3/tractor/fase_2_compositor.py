from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
)
import os

from generator.v3.adapter.persistir_adapter import persistir_video_v3


# -------------------------------------------------
# FASE 2 — Composición de layers sobre fondo fijo
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
    print("[LONG TRACTOR] FASE 2 — COMPOSITOR DE LAYERS")
    print("[LONG TRACTOR] Modo test:", modo_test)

    if not modo_test:
        raise RuntimeError("FASE 2 solo permitida en modo test")

    # -------------------------------------------------
    # 1. Configuración base
    # -------------------------------------------------
    WIDTH = 1920
    HEIGHT = 1080
    DURACION_LAYER = 3  # segundos por layer
    FADE_SECONDS = 0.4

    layers_path = resolved_config["content"]["layers_path"]
    background_path = resolved_config["visual"]["background_test"]

    # -------------------------------------------------
    # 2. Cargar background fijo
    # -------------------------------------------------
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background no encontrado: {background_path}")

    print("[FASE 2] Background:", background_path)

    # Cargamos background SIN duración aún
    background = (
        ImageClip(background_path)
        .resize((WIDTH, HEIGHT))
    )

    # -------------------------------------------------
    # 3. Cargar layers PNG
    # -------------------------------------------------
    layer_files = sorted(
        f for f in os.listdir(layers_path)
        if f.lower().endswith(".png")
    )

    if not layer_files:
        raise RuntimeError("No se encontraron layers PNG")

    print(f"[FASE 2] Layers encontrados: {len(layer_files)}")

    clips = []
    current_time = 0.0

    for fname in layer_files:
        layer_path = os.path.join(layers_path, fname)

        print(f"[FASE 2] Layer → {fname} @ {current_time:.2f}s")

        clip = (
            ImageClip(layer_path)
            .set_start(current_time)
            .set_duration(DURACION_LAYER)
            .fadein(FADE_SECONDS)
            .fadeout(FADE_SECONDS)
        )

        clips.append(clip)
        current_time += DURACION_LAYER

    DURACION_TOTAL = current_time

    # -------------------------------------------------
    # 4. Ajustar duración del background
    # -------------------------------------------------
    background = background.set_duration(DURACION_TOTAL)

    # -------------------------------------------------
    # 5. Composición final
    # -------------------------------------------------
    video = CompositeVideoClip(
        [background] + clips,
        size=(WIDTH, HEIGHT)
    ).set_duration(DURACION_TOTAL)

    # -------------------------------------------------
    # 6. Render
    # -------------------------------------------------
    print("[FASE 2] Renderizando video...")
    print("[FASE 2] Duración total:", DURACION_TOTAL, "seg")

    video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=4,
    )

    # -------------------------------------------------
    # 7. Persistencia mínima
    # -------------------------------------------------
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo="long_tractor_oracion",
        output_path=output_path,
        texto="FASE 2 — Composición de layers",
        imagen_usada=os.path.basename(background_path),
        musica_usada=None,
        fingerprint=None,
        usar_tts=False,
        modo_test=True,
        licencia_path=None,
    )

    print("[LONG TRACTOR] FASE 2 OK — Composición validada")
