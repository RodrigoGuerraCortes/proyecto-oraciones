# config/config_resolver.py

import os

from db.repositories.channel_config_repo import get_channel_config
from config.resolve_long_config import resolve_long_config
from config.resolve_short_config import resolve_short_config
from config.resolve_tractor_config import resolve_tractor_config


def resolver_config(
    *,
    channel_id: int,
    format_code: str,
    tractor: str | None = None,
) -> dict:

    base_storage_path = os.getenv("BASE_STORAGE_PATH")
    if not base_storage_path:
        raise RuntimeError("BASE_STORAGE_PATH no definido")

    channel_config = get_channel_config(channel_id)

    formats = channel_config.get("formats", {})


    if format_code not in formats:
        raise KeyError(f"Formato no encontrado: {format_code}")

    fmt = formats[format_code]
    engine = fmt.get("engine")

    if engine == "short_plain" or engine == "short_stanza":
        return resolve_short_config(
            channel_config=channel_config,
            format_code=format_code,
            base_storage_path=base_storage_path,
        )

    if engine == "long_guided":
        return resolve_long_config(
            channel_config=channel_config,
            format_code=format_code,
            base_storage_path=base_storage_path,
        )



    if engine == "long_tractor":

        print("Tractor : ", tractor)

        return resolve_tractor_config(
            channel_config=channel_config,
            format_code=format_code,
            base_storage_path=base_storage_path,
            tractor=tractor,
        )

    raise ValueError(f"Engine no soportado: {engine}")
