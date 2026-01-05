# generator/v3/generator/cleanup.py
import os
from PIL import Image, UnidentifiedImageError
import sys

def limpiar_temporales( base_path_assest: str):

    print("\n============================")
    print(" [CLEAN] Limpiando archivos temporales...")
    print("============================")

    print(f"[CLEAN] Base path: {base_path_assest}\n")

    archivos_temp = [
        f"{base_path_assest}/tmp/fondo_tmp.jpg",
        f"{base_path_assest}/tmp/grad_tmp.png",
        f"{base_path_assest}/tmp/titulo.png",
        f"{base_path_assest}/tmp/intro_txt.png",
        "bloque.png",
        "estrofa.png",
    ]

    for f in archivos_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"[CLEAN] Eliminado {f}")
            except Exception:
                pass

    #try:
    #    if os.path.isdir("videos"):
    #        for f in os.listdir("videos"):
    #            if "TEMP_MPY" in f or f.endswith(".png") or f.endswith(".jpg"):
    #                path = os.path.join("videos", f)
    #                if not path.endswith(".mp4"):
    #                    try:
    #                        os.remove(path)
    #                        print(f"[CLEAN] Eliminado {path}")
    #                    except Exception:
    #                        pass
    #except Exception:
    #    pass


def limpiar_imagenes_corruptas():
    carpeta = "imagenes"
    if not os.path.isdir(carpeta):
        print("[CHECK] Carpeta imagenes/ no existe")
        return

    print("\n============================")
    print(" [CHECK] Verificando imágenes corruptas...")
    print("============================")

    buenas = 0
    malas = 0

    for item in os.listdir(carpeta):
        path = os.path.join(carpeta, item)

        # 🔒 ignorar carpetas (MUY IMPORTANTE)
        if os.path.isdir(path):
            continue

        # ignorar vignette
        if item.lower() == "vignette.png":
            continue

        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im2:
                im2.convert("RGB")
            buenas += 1

        except (UnidentifiedImageError, OSError, IOError) as e:
            print(f"[CORRUPTA] {item} → eliminado ({e})")
            try:
                os.remove(path)
                malas += 1
            except Exception:
                print(f"[ERROR] No se pudo eliminar {item}")

    print(f"\n[CHECK] Imágenes válidas: {buenas}")
    print(f"       Imágenes corruptas eliminadas: {malas}\n")
