# generator/decision.py

from generator.selector import elegir_imagen_por_categoria
from generator.categoria import decidir_categoria_video
import os

def decidir_imagen_video(tipo: str, titulo: str, texto: str, base_path_assest: str) -> str:

    print(f"[DECIDE] Decidiendo imagen para video tipo={tipo}")

    categoria = decidir_categoria_video(tipo, titulo, texto)

    print(f"[DECIDE] Categoría elegida: {categoria}")

    if not os.path.isdir(os.path.join(base_path_assest, categoria)):
        categoria = "jesus"  # fallback absoluto

    ruta_img, _ = elegir_imagen_por_categoria(categoria, base_path_assest=base_path_assest)

    print(f"[DECIDE] Imagen elegida: {ruta_img}")

    return ruta_img