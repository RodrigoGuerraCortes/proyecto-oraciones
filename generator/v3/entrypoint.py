# generator/v3/entrypoint.py

import argparse
import os

from dotenv import load_dotenv

from generator.v3.config.config_resolver import resolver_config
from generator.v3.wrappers.generar_oracion import generar_oracion_v3
from generator.v3.wrappers.generar_salmo import generar_salmo_v3
from generator.v3.long.generar_long_oracion_generico import generar_long_oracion_generico
import uuid


load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline v3 – Generación de videos"
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
        help="Código de formato (ej: short_oracion, long_oracion_guiada)",
    )

    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Archivo de texto a usar",
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
        help="Forzar TTS",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # ---------------------------------------------------------
    # Resolver config V3 (UNA sola vez)
    # ---------------------------------------------------------
    resolved_config = resolver_config(
        channel_id=args.channel,
        format_code=args.format,
    )

    format_cfg = resolved_config["format"]
    format_type = format_cfg["type"]

    print("[ENTRYPOINT]")
    print(" - channel:", args.channel)
    print(" - format_code:", args.format)
    print(" - format_type:", format_type)
    print(" - output:", args.out)

    # ---------------------------------------------------------
    # Routing por tipo de formato
    # ---------------------------------------------------------
    if format_type == "short":
        # wrappers existentes
        if args.format == "short_oracion":
            generar_oracion_v3(
                channel_id=args.channel,
                text_filename=args.text,
                output_path=args.out,
                modo_test=args.test,
                force_tts=True if args.force_tts else None,
            )

        elif args.format == "short_salmo":
            generar_salmo_v3(
                channel_id=args.channel,
                text_filename=args.text,
                output_path=args.out,
                modo_test=args.test,
                force_tts=True if args.force_tts else None,
            )

        else:
            raise ValueError(f"Wrapper short no soportado: {args.format}")

    elif format_type == "long":
        if args.format == "long_oracion_guiada":
            generar_long_oracion_generico(
                resolved_config=resolved_config,
                text_filename=args.text,
                output_path=args.out,
                video_id=str(uuid.uuid4()),
                channel_id=args.channel,
                modo_test=args.test,
                force_tts=True if args.force_tts else None,
            )

    else:
        raise ValueError(f"Tipo de formato no soportado: {format_type}")

    print("[V3] Video generado correctamente")


if __name__ == "__main__":
    main()
