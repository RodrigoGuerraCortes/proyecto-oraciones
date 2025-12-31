# generator/v3/config/config_resolver.py

import os

from db.repositories.channel_config_repo import get_channel_config
from generator.v3.config.resolve_long_config import resolve_long_config
from generator.v3.config.resolve_short_config import resolve_short_config


def resolver_config(
    *,
    channel_id: int,
    format_code: str,
) -> dict:
    """
    Resolver central V3.
    Decide si el formato es short o long.
    """

    base_storage_path = os.getenv("BASE_STORAGE_PATH")
    if not base_storage_path:
        raise RuntimeError("BASE_STORAGE_PATH no definido")

    channel_config = get_channel_config(channel_id)

    formats = channel_config.get("formats", {})
    if format_code not in formats:
        raise KeyError(f"Formato no encontrado: {format_code}")

    fmt = formats[format_code]
    format_type = fmt.get("format", "short")

    if format_type == "short":
        return resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
            base_storage_path=base_storage_path,
        )

    if format_type == "long":
        return resolve_long_config(
            channel_config=channel_config,
            format_code=format_code,
            base_storage_path=base_storage_path,
        )

    raise ValueError(f"Tipo de formato no soportado: {format_type}")
