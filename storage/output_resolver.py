# storage/output_resolver.py
import os
from config.storage import BASE_STORAGE_PATH


def resolve_output_path(
    *,
    override_out: str | None,
    channel_code: str,
    format_type: str,
    video_id: str,
    slug: str | None = None,
) -> str:
    """
    Resuelve el path final de salida del video.
    """

    if override_out:
        return override_out

    categoria = "shorts" if format_type.startswith("short") else "longs"

    filename = f"{video_id}__{slug}.mp4"

    return os.path.join(
        BASE_STORAGE_PATH,
        "generated",
        channel_code,
        categoria,
        filename,
    )
