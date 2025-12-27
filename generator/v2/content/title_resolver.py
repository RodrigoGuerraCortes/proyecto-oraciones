# generator/v2/content/title_resolver.py

import os
from generator.v2.video.title_renderer import normalize_title


def construir_titulo_desde_archivo(path: str) -> str:
    nombre = os.path.basename(path)
    nombre = os.path.splitext(nombre)[0]

    # quitar UUID si existe
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]

    texto = nombre.replace("_", " ").strip()
    return normalize_title(texto)


def resolve_title(
    *,
    parsed_title: str | None,
    path_txt: str,
) -> str:
    """
    Estrategia:
    1) Título semántico (contenido)
    2) Filename normalizado (fallback)
    """
    if parsed_title:
        return normalize_title(parsed_title)

    return construir_titulo_desde_archivo(path_txt)
