# generator/image/decision.py

from generator.image.selector import elegir_imagen_por_categoria
from generator.content.categoria import decidir_categoria_video
import os

IMAGENES_BASE = "imagenes"

def decidir_imagen_video(tipo: str, titulo: str, texto: str) -> str:
    categoria = decidir_categoria_video(tipo, titulo, texto)

    if not os.path.isdir(os.path.join(IMAGENES_BASE, categoria)):
        categoria = "jesus"  # fallback absoluto

    ruta_img, _ = elegir_imagen_por_categoria(categoria)
    return ruta_img