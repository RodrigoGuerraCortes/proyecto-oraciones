# generator/v3/entrypoint.py

import argparse
import uuid
import os

from dotenv import load_dotenv

from generator.v3.config.config_resolver import resolver_config
from generator.v3.engine.registry import ENGINE_REGISTRY

load_dotenv()


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline v3 – Generación de videos (genérico)"
    )

    parser.add_argument(
        "--channel",
        type=int,
        required=True,
        help="ID del canal",
    )

    parser.add_argument(
        "--format",
        type=str,
        required=True,
        help="Código de formato (ej: short_oracion, short_salmo, long_guiado)",
    )

    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Archivo de texto a usar (filename o path relativo según engine)",
    )

    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Ruta del archivo de salida (.mp4)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo test (duraciones mínimas)",
    )

    parser.add_argument(
        "--force-tts",
        action="store_true",
        help="Forzar TTS (override config)",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    args = parse_args()

    # ---------------------------------------------------------
    # Resolver config (UNA sola vez)
    # ---------------------------------------------------------
    resolved_config = resolver_config(
        channel_id=args.channel,
        format_code=args.format,
    )

    format_cfg = resolved_config["format"]
    engine_code = format_cfg.get("engine")
    format_type = format_cfg.get("type")

    print("Audio Music Path:", resolved_config["audio"]["music"]["base_path"])
    
    music_path = resolved_config["audio"]["music"]["base_path"]

    if not engine_code:
        raise RuntimeError(
            f"El formato '{args.format}' no define 'engine' en la config"
        )

    generator_fn = ENGINE_REGISTRY.get(engine_code)

    if not generator_fn:
        raise RuntimeError(
            f"Engine '{engine_code}' no registrado en ENGINE_REGISTRY"
        )

    video_id = str(uuid.uuid4())


    # 3. Resolver paths
    text_path = os.path.join(
        resolved_config["content"]["base_path"],
        args.text,
    )

    print("[ENTRYPOINT V3]")
    print(" - channel_id:", args.channel)
    print(" - format_code:", args.format)
    print(" - format_type:", format_type)
    print(" - engine:", engine_code)
    print(" - text:", text_path)
    print(" - output:", args.out)
    print(" - test:", args.test)
    print(" - force_tts:", args.force_tts)
    print(" - video_id:", video_id)

    # ---------------------------------------------------------
    # Ejecución del engine (GENÉRICA)
    # ---------------------------------------------------------
    generator_fn(
        resolved_config=resolved_config,
        text_path=text_path,
        output_path=args.out,
        video_id=video_id,
        channel_id=args.channel,
        modo_test=args.test,
        force_tts=True if args.force_tts else None,
        music_path=music_path,
    )

    print("[V3] Video generado correctamente")


if __name__ == "__main__":
    main()
