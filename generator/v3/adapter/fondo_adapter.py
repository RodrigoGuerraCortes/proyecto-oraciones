# generator/v3/adapter/fondo_adapter.py

import os
import tempfile
from contextlib import contextmanager

from generator.image.fondo import crear_fondo as crear_fondo_v1


@contextmanager
def imagenes_symlink(base_path: str):
    """
    Crea un symlink temporal 'imagenes' apuntando a base_path
    y lo elimina al salir.
    """
    link_name = "imagenes"

    already_exists = os.path.exists(link_name)

    if not already_exists:
        os.symlink(base_path, link_name)

    try:
        yield
    finally:
        if not already_exists and os.path.islink(link_name):
            os.unlink(link_name)


def crear_fondo_v3(
    *,
    duracion: float,
    ruta_imagen: str,
    base_path: str,
):
    if not base_path:
        raise ValueError("base_path es obligatorio en v3")

    ruta_absoluta = os.path.join(base_path, ruta_imagen)

    if not os.path.exists(ruta_absoluta):
        raise FileNotFoundError(ruta_absoluta)

    # v1 cree que trabaja con ./imagenes
    with imagenes_symlink(base_path):
        return crear_fondo_v1(duracion, ruta_imagen)
