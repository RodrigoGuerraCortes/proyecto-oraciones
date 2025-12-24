# generator/v2/content/selector_simple.py

import os
import random
from typing import Tuple


def elegir_texto_simple(
    *,
    base_path: str,
    sub_path: str,
) -> Tuple[str, str]:
    """
    Selector v2 SIMPLE.
    No usa BD.
    No aplica reglas.
    Solo filesystem.
    """

    carpeta = os.path.join(base_path, sub_path)

    if not os.path.isdir(carpeta):
        raise RuntimeError(f"Carpeta de textos no existe: {carpeta}")

    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]

    if not archivos:
        raise RuntimeError("No hay textos disponibles")

    elegido = random.choice(archivos)
    path = os.path.join(carpeta, elegido)

    base_name = elegido.replace(".txt", "")
    return path, base_name
