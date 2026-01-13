"""
FASE 1.6 — Expansión del tractor por repetición controlada

- NO duplica archivos
- Construye una secuencia lógica expandida
- Respeta bloques no repetibles
"""

import os
import json
from moviepy.editor import AudioFileClip
import sys

def expandir_tractor(
    *,
    resolved_config: dict,
    layers_path: str,
    audio_path: str,
    output_sequence_path: str,
):
    
    print("[FASE 1.6] Iniciando expansión del tractor...")
    print("[FASE 1.6] Layers path:", layers_path)
    print("[FASE 1.6] Audio path:", audio_path)
    print("[FASE 1.6] Output sequence path:", output_sequence_path)

    content_cfg = resolved_config["content"]
    target_minutes = resolved_config.get("target_duration_minutes", 55)

    blocks = content_cfg["blocks"]
    repeatable_blocks = content_cfg.get("repeatable_blocks", [])
    silence_rules = content_cfg.get("silence_rules", [])

    print("[FASE 1.6] Silence rules:", silence_rules)
    
    silence_after_block = {
        r["after_block"]: float(r["duration_seconds"])
        for r in silence_rules
        if "after_block" in r
    }

    cycle_silence = next(
        (float(r["duration_seconds"])
        for r in silence_rules
        if r.get("after_every_cycle")),
        0.0
    )

    # -------------------------------------------------
    # 1. Mapear layers por bloque
    # -------------------------------------------------
    layer_files = sorted(
        f for f in os.listdir(layers_path)
        if f.endswith(".png")
    )

    if not layer_files:
        raise RuntimeError("No se encontraron layers base")

    layers_by_block = {}

    for fname in layer_files:
        parts = fname.split("_", 2)
        if len(parts) < 3:
            raise RuntimeError(f"Nombre de layer inválido: {fname}")

        block_key = parts[1]  # ej: 03
        layers_by_block.setdefault(block_key, []).append(fname)

    # -------------------------------------------------
    # 2. Calcular duración por bloque
    # -------------------------------------------------
    block_durations = {}

    for block_key, files in layers_by_block.items():
        total = 0.0
        for f in files:
            wav = os.path.join(audio_path, f.replace(".png", ".mp3"))
            if not os.path.exists(wav):
                raise FileNotFoundError(wav)

            with AudioFileClip(wav) as a:
                total += a.duration

        block_durations[block_key] = total

    # -------------------------------------------------
    # 3. Construir bloques base
    # -------------------------------------------------
    def key_from_txt(txt):
        return txt.split("_", 1)[0]  # "03"

    apertura_keys = [key_from_txt(blocks[0])]
    cierre_keys = [key_from_txt(blocks[-1])]

    repeatable_keys = [
        key_from_txt(b) for b in repeatable_blocks
    ]

    fixed_middle_keys = [
        key_from_txt(b)
        for b in blocks[1:-1]
        if key_from_txt(b) not in repeatable_keys
    ]

    # -------------------------------------------------
    # 4. Duración base
    # -------------------------------------------------
    base_keys = apertura_keys + fixed_middle_keys + cierre_keys
   #base_duration = sum(block_durations[k] for k in base_keys)

    base_duration = 0.0

    for k in base_keys:
        base_duration += block_durations[k]

        # silencio después del bloque
        if k in silence_after_block:
            base_duration += silence_after_block[k]


    target_seconds = target_minutes * 60
    remaining = target_seconds - base_duration

    if remaining <= 0:
        raise RuntimeError("La duración base ya supera el target")

    # -------------------------------------------------
    # 5. Construir ciclos repetibles
    # -------------------------------------------------

    if repeatable_keys:
        cycle_duration = sum(block_durations[k] for k in repeatable_keys)
        cycle_duration += cycle_silence

        cycles_needed = int(remaining // cycle_duration) + 1
    else:
        cycles_needed = 0
    # -------------------------------------------------
    # 6. Construir SECUENCIA FINAL
    # -------------------------------------------------
    sequence = []

    # apertura
    for k in apertura_keys:
        for fname in layers_by_block[k]:
            sequence.append(fname.replace(".png", ""))

        if k in silence_after_block:
            sequence.append({
                "type": "silence",
                "duration_seconds": silence_after_block[k]
            })

    # ciclos
    for _ in range(cycles_needed):
        for k in repeatable_keys:
            for fname in layers_by_block[k]:
                sequence.append(fname.replace(".png", ""))

        if cycle_silence > 0:
            sequence.append({
                "type": "silence",
                "duration_seconds": cycle_silence
            })

    # cierre
    for k in cierre_keys:
        for fname in layers_by_block[k]:
            sequence.append(fname.replace(".png", ""))

    # -------------------------------------------------
    # 7. Medir duración final
    # -------------------------------------------------
    expanded_duration = 0.0

    for item in sequence:
        if isinstance(item, dict) and item.get("type") == "silence":
            expanded_duration += float(item["duration_seconds"])
        else:
            wav = os.path.join(audio_path, item + ".mp3")
            with AudioFileClip(wav) as a:
                expanded_duration += a.duration

    # -------------------------------------------------
    # 8. Guardar resultado
    # -------------------------------------------------
    os.makedirs(os.path.dirname(output_sequence_path), exist_ok=True)

    with open(output_sequence_path + '/sequence.json', "w", encoding="utf-8") as f:
        json.dump(
            {
                "target_minutes": target_minutes,
                "base_duration_sec": round(base_duration, 2),
                "expanded_duration_sec": round(expanded_duration, 2),
                "cycles": cycles_needed,
                "sequence": sequence,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("[FASE 1.6] Expansión completada")
    print("[FASE 1.6] Ciclos:", cycles_needed)
    print("[FASE 1.6] Duración final:", round(expanded_duration / 60, 2), "min")
