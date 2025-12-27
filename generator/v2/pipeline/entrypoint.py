# generator/v2/pipeline/entrypoint.py

import argparse

from generator.v2.pipeline.short_pipeline import run_short_pipeline
from db.repositories.channel_config_repo import get_channel_config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline v2 – Generación de videos (DEV)"
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
        help="Código de formato (ej: short_oracion, short_salmo)",
    )

    parser.add_argument(
        "--qty",
        type=int,
        default=1,
        help="Cantidad de videos a generar",
    )

    parser.add_argument(
        "--text",
        type=str,
        help="Archivo de texto específico a usar (solo DEV/TEST)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo test (paths de test, sin persistencia)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    channel_config = get_channel_config(args.channel)

    run_short_pipeline(
        channel_config=channel_config,
        channel_id=args.channel,
        format_code=args.format,
        quantity=args.qty,
        modo_test=args.test,
        force_text=args.text,
    )


if __name__ == "__main__":
    main()
