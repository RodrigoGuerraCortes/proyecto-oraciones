# generator/v3/wrappers/generar_salmo.py

import os
import uuid

from db.repositories.channel_config_repo import get_channel_config
from generator.v3.config.config_resolver import resolve_short_config
from generator.v3.short.generar_short_stanza_generico import generar_short_stanza_generico


def generar_salmo_v3(
    *,
    channel_id: int,
    text_filename: str,
    output_path: str,
    modo_test: bool = False,
    force_tts: bool | None = None,
):
    base_storage_path = os.getenv("BASE_STORAGE_PATH")
    if not base_storage_path:
        raise RuntimeError("BASE_STORAGE_PATH no definido")

    channel_config = get_channel_config(channel_id)

    resolved_config = resolve_short_config(
        channel_config=channel_config,
        format_code="short_salmo",
        base_storage_path=base_storage_path,
    )

    text_path = os.path.join(
        resolved_config["content"]["base_path"],
        text_filename,
    )

    video_id = str(uuid.uuid4())

    generar_short_stanza_generico(
        resolved_config=resolved_config,
        text_path=text_path,
        output_path=output_path,
        video_id=video_id,
        modo_test=modo_test,
        force_tts=force_tts,
        channel_id=channel_id,
    )
