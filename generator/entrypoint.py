#!/usr/bin/env python3
import sys
from generator.pipeline import generar_videos
from generator.cleanup import limpiar_imagenes_corruptas

MODO_TEST = False


def main():
    global MODO_TEST

    limpiar_imagenes_corruptas()

    if "test" in sys.argv:
        MODO_TEST = True
        print("⚠ MODO TEST ACTIVADO")

    if len(sys.argv) < 3:
        print("Uso:")
        print("  python3 entrypoint.py 4 oracion")
        print("  python3 entrypoint.py 2 salmo")
        sys.exit(1)

    cantidad = int(sys.argv[1])
    tipo = sys.argv[2].lower()

    if tipo not in ("oracion", "salmo"):
        print("ERROR: tipo inválido")
        sys.exit(1)

    generar_videos(tipo, cantidad, modo_test=MODO_TEST)


if __name__ == "__main__":
    main()
