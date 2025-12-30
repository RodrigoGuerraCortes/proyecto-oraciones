# generator/v3/wrappers/generar_oracion.py

import os
import uuid

from db.repositories.channel_config_repo import get_channel_config
from generator.v3.config.config_resolver import resolve_short_config
from generator.v3.short.generar_short_plain_generico import generar_short_plain


def generar_oracion_v3(
    *,
    channel_id: int,
    text_filename: str,
    output_path: str,
    modo_test: bool = False,
    force_tts: bool | None = None,
):
    """
    Wrapper semántico temporal para 'short_oracion'.

    NO contiene lógica de render.
    NO contiene lógica de audio.
    NO contiene lógica de persistencia.
    """

    base_storage_path = os.getenv("BASE_STORAGE_PATH")
    if not base_storage_path:
        raise RuntimeError("BASE_STORAGE_PATH no definido")

    # 1. Cargar config del canal
    channel_config = get_channel_config(channel_id)

    # 2. Resolver config del formato
    resolved_config = resolve_short_config(
        channel_config=channel_config,
        format_code="short_oracion",
        base_storage_path=base_storage_path,
    )

    # 3. Resolver paths
    text_path = os.path.join(
        resolved_config["content"]["base_path"],
        text_filename,
    )

    # 4. Generar ID
    video_id = str(uuid.uuid4())

    # 5. Delegar al pipeline genérico
    generar_short_plain(
        resolved_config=resolved_config,
        text_path=text_path,
        output_path=output_path,
        video_id=video_id,
        modo_test=modo_test,
        force_tts=force_tts,
        channel_id=channel_id,
    )
