"""
FASE 1.5 — Generación de TTS por layer

- Un WAV por cada PNG generado en FASE 1
- Naming 1:1 (misma base)
- Persistente (build artifacts)
- No video, no MoviePy
"""

import os
import asyncio
import edge_tts

# -------------------------------------------------
# Configuración base
# -------------------------------------------------
DEFAULT_VOICE = "es-MX-JorgeNeural"
DEFAULT_RATE = "-8%"
DEFAULT_VOLUME = "+0%"
# Si habilitas pitch:
DEFAULT_PITCH = "-2Hz"

# -------------------------------------------------
# Utilidad: generar un WAV con edge-tts
# -------------------------------------------------
async def _tts_to_wav(
    *,
    text: str,
    output_wav: str,
    voice: str,
    rate: str,
    volume: str,
    pitch: str,
):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(output_wav)


# -------------------------------------------------
# Entrada principal FASE 1.5
# -------------------------------------------------
def generar_tts_layers(
    *,
    resolved_config: dict,
    layers_path: str,
    audio_output_path: str,
    force: bool = False,
):
    """
    Genera un WAV por cada layer PNG existente.
    El texto se obtiene desde los mismos TXT y sub-bloques
    usados en FASE 1.
    """

    content_cfg = resolved_config["content"]
    audio_cfg = resolved_config["audio"]
    tts_cfg = audio_cfg.get("tts", {})

    base_text_path = content_cfg["base_path"]
    blocks = content_cfg["blocks"]

    voice = tts_cfg.get("voice", DEFAULT_VOICE)
    rate = tts_cfg.get("rate", DEFAULT_RATE)
    volume = tts_cfg.get("volume", DEFAULT_VOLUME)
    

    os.makedirs(audio_output_path, exist_ok=True)

    # -------------------------------------------------
    # 1. Reconstruir EXACTAMENTE el orden de sub-bloques
    # -------------------------------------------------
    ordered_text_blocks = []

    for block_file in blocks:
        txt_path = os.path.join(base_text_path, block_file)

        if not os.path.exists(txt_path):
            raise FileNotFoundError(txt_path)

        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        sub_blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

        for sub_idx, block_text in enumerate(sub_blocks, start=1):
            ordered_text_blocks.append(
                {
                    "block_file": block_file.replace(".txt", ""),
                    "sub_idx": sub_idx,
                    "text": block_text,
                }
            )

    # -------------------------------------------------
    # 2. Validar correspondencia PNG ↔ texto
    # -------------------------------------------------
    layer_files = sorted(
        f for f in os.listdir(layers_path)
        if f.lower().endswith(".png")
    )

    if len(layer_files) != len(ordered_text_blocks):
        raise RuntimeError(
            f"Desfase layers/texto: "
            f"{len(layer_files)} PNG vs "
            f"{len(ordered_text_blocks)} textos"
        )

    print("[FASE 1.5] Generando TTS por layer...")
    print("[FASE 1.5] Voice:", voice)

    # -------------------------------------------------
    # 3. Generar WAVs (1:1)
    # -------------------------------------------------
    for idx, (png_name, text_info) in enumerate(
        zip(layer_files, ordered_text_blocks),
        start=1,
    ):
        wav_name = png_name.replace(".png", ".wav")
        wav_path = os.path.join(audio_output_path, wav_name)

        if os.path.exists(wav_path) and not force:
            print(f"  ⏭️  {wav_name} ya existe, se omite")
            continue

        text = text_info["text"]

        print(f"  🔊 [{idx:04d}] {wav_name}")
        asyncio.run(
            _tts_to_wav(
                text=text,
                output_wav=wav_path,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=DEFAULT_PITCH
            )
        )

    print("[FASE 1.5] TTS generado correctamente")
