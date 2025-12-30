# generator/v3/entrypoint.py

import argparse
import os

from dotenv import load_dotenv

from generator.v3.wrappers.generar_oracion import generar_oracion_v3
# futuros:
# from generator.v3.wrappers.generar_salmo import generar_salmo_v3
from generator.v3.short.generar_short_stanza_generico import generar_short_stanza_generico


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
        help="Código de formato (ej: short_oracion)",
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
    # Routing por formato (temporal)
    # ---------------------------------------------------------
    if args.format == "short_oracion":
        generar_oracion_v3(
            channel_id=args.channel,
            text_filename=args.text,
            output_path=args.out,
            modo_test=args.test,
            force_tts=True if args.force_tts else None,
        )
    elif args.format == "short_salmo":
        generar_short_stanza_generico(
            channel_id=args.channel,
            text_filename=args.text,
            output_path=args.out,
            modo_test=args.test,
            force_tts=True if args.force_tts else None,
        )
    else:
        raise ValueError(f"Formato no soportado aún: {args.format}")

    print("[V3] Video generado correctamente")


if __name__ == "__main__":
    main()
