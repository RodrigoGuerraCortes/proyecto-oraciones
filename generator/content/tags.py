
# generator/content/tags.py

import os
# =====================================================================
#   TAGS (solo usados en YouTube)
# =====================================================================
def generar_tags_from_descripcion(descripcion):
    """
    Extrae hashtags → los transforma en tags de YouTube.
    """
    palabras = descripcion.split()
    hashtags = [p for p in palabras if p.startswith("#")]
    tags = [h[1:] for h in hashtags]

    # Sin duplicados
    return list(dict.fromkeys(tags))
