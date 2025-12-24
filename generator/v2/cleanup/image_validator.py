# generator/v2/cleanup/image_validator.py

import os
from PIL import Image, UnidentifiedImageError


def validate_images_in_directory(
    *,
    directory: str,
    ignore_files: list[str] | None = None,
) -> dict:
    """
    Valida imágenes de un directorio.
    Retorna métricas, no imprime.
    """
    ignore_files = ignore_files or []
    valid = 0
    removed = 0

    if not os.path.isdir(directory):
        return {
            "valid": 0,
            "removed": 0,
            "error": "directory_not_found",
        }

    for name in os.listdir(directory):
        if name in ignore_files:
            continue

        path = os.path.join(directory, name)

        if os.path.isdir(path):
            continue

        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im2:
                im2.convert("RGB")
            valid += 1

        except (UnidentifiedImageError, OSError, IOError):
            try:
                os.remove(path)
                removed += 1
            except Exception:
                pass

    return {
        "valid": valid,
        "removed": removed,
    }
