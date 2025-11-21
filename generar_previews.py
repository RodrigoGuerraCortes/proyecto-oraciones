import os
import sys
from generar_video import (
    crear_fondo,
    crear_imagen_texto,
    crear_imagen_titulo,
    ANCHO,
    ALTO
)
from PIL import Image


# ============================================================
#           GENERAR PREVIEW DE UNA ORACIÓN (IMAGEN)
# ============================================================
def generar_preview_oracion(path_in, path_out):
    # texto completo
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    # título desde el nombre
    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    # 1) Fondo + gradiente (llamamos directamente tu función)
    fondo, grad_clip = crear_fondo(30)

    # Convertimos gradiente a PIL y lo mezclamos
    grad_img = grad_clip.get_frame(0)
    grad_pil = Image.fromarray(grad_img)

    # Fondo PIL
    fondo_pil = Image.fromarray(fondo.get_frame(0))

    # Asegurarse de que grad_pil tenga el mismo tamaño que fondo_pil antes de mezclar
    if fondo_pil.size != grad_pil.size:
        grad_pil = grad_pil.resize(fondo_pil.size)

    # Mezclamos fondo + gradiente
    fondo_pil = Image.alpha_composite(fondo_pil.convert("RGBA"), grad_pil.convert("RGBA"))

    # 2) Renderizar título
    titulo_path = "textos/preview_titulo.png"
    crear_imagen_titulo(titulo, titulo_path)
    titulo_img = Image.open(titulo_path).convert("RGBA")

    # 3) Renderizar texto principal
    texto_path = "textos/preview_texto.png"
    crear_imagen_texto(texto, texto_path)
    texto_img = Image.open(texto_path).convert("RGBA")

    # 4) Componer todo en una imagen final
    canvas = fondo_pil.convert("RGBA")

    # Posicionar título
    canvas.alpha_composite(titulo_img, (0, 120))

    # Posicionar texto centrado vertical
    y_texto = int((ALTO - texto_img.height) // 2) + 60
    canvas.alpha_composite(texto_img, (0, y_texto))

    # 5) Guardar preview final
    canvas.save(path_out)
    print(f"📸 Preview generada → {path_out}")


# ============================================================
#      COMANDO PRINCIPAL: generar varias previews
# ============================================================
def generar_previews(cantidad):
    carpeta = "textos/oraciones"
    archivos = os.listdir(carpeta)
    seleccion = archivos[:cantidad]

    os.makedirs("previews", exist_ok=True)

    for archivo in seleccion:
        path_in = f"{carpeta}/{archivo}"
        nombre = os.path.splitext(archivo)[0]
        path_out = f"previews/{nombre}.png"

        generar_preview_oracion(path_in, path_out)


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    generar_previews(cantidad)
