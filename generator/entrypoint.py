#!/usr/bin/env python3
import sys

from generator.pipeline import generar_videos
from generator.oso import generar_oso
from generator.cleanup import limpiar_imagenes_corruptas

MODO_TEST = False


def main():
    global MODO_TEST

    limpiar_imagenes_corruptas()

    # -------------------------------------------------
    # Flags
    # -------------------------------------------------
    if "test" in sys.argv:
        MODO_TEST = True
        print("⚠ MODO TEST ACTIVADO")

    # -------------------------------------------------
    # Validación básica
    # -------------------------------------------------
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python3 entrypoint.py 4 oracion")
        print("  python3 entrypoint.py 2 salmo")
        print("  python3 entrypoint.py 1 oso")
        print("  python3 entrypoint.py 2 oso test")
        sys.exit(1)

    try:
        cantidad = int(sys.argv[1])
    except ValueError:
        print("ERROR: cantidad debe ser un número")
        sys.exit(1)

    tipo = sys.argv[2].lower()

    # -------------------------------------------------
    # Dispatch por tipo
    # -------------------------------------------------
    if tipo == "oso":
        generar_oso(cantidad, modo_test=MODO_TEST)
        return

    if tipo in ("oracion", "salmo"):
        generar_videos(tipo, cantidad, modo_test=MODO_TEST)
        return
    
    if tipo in ("oracion", "salmo", "oracion_long"):
        generar_videos(tipo, cantidad, modo_test=MODO_TEST)
        return
        # aquí podrías integrar con tu generar_videos() si lo tienes por pipeline.
        # por ahora, llamada directa si quieres:
        # generar_oracion_long(video_id=..., path_in=..., path_out=..., ...)


    print("ERROR: tipo inválido (use oracion, salmo u oso)")
    sys.exit(1)


if __name__ == "__main__":
    main()
