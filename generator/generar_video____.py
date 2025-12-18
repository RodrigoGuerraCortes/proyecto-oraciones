# ==========================================================
# GENERATOR · GENERAR VIDEO (UNIDAD ATÓMICA)
# ==========================================================
# - Genera UN video MP4 desde UN texto (oración o salmo)
# - NO decide cantidad
# - NO decide horarios
# - NO publica
# ==========================================================

import os
import sys

from historial import (
    registrar_video_generado,
    tag_ya_existe,
)

from generator.content.fingerprinter import generar_tag_inteligente
from generator.cleanup import limpiar_temporales
from generator.image.fondo import crear_fondo, get_ultima_imagen_usada
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio

# -----------------------------
# CONFIG DE GENERACIÓN
# -----------------------------
CTA_DUR = 5
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 16
ORACION_DURACION = 25  # simple por ahora; si tienes calculadora, muévela a duration.py

MODO_TEST = False


def _asegurar_dirs():
    os.makedirs("videos/oraciones", exist_ok=True)
    os.makedirs("videos/salmos", exist_ok=True)


def generar_oracion_desde_txt(path_txt: str) -> str:
    _asegurar_dirs()

    with open(path_txt, encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_txt))[0]
    salida = f"videos/oraciones/{base}.mp4"

    duracion = 5 if MODO_TEST else ORACION_DURACION

    # 1) Fondo + gradiente (media.py debería retornar también imagen usada)
    fondo, grad, imagen_usada = crear_fondo(duracion)

    # 2) Render texto
    titulo = base.replace("_", " ").title()
    crear_imagen_titulo(titulo, "titulo.png")
    crear_imagen_texto(texto, "bloque.png")

    # 3) Audio (media.py debería retornar música usada)
    audio, musica_usada = crear_audio(duracion + CTA_DUR)

    # 4) Tag único
    tag = generar_tag_inteligente(
        tipo="oracion",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=duracion + CTA_DUR,
    )

    # Evitar colisión por seguridad
    intentos = 0
    while tag_ya_existe(tag) and intentos < 5:
        fondo, grad, imagen_usada = crear_fondo(duracion)     # cambia imagen
        audio, musica_usada = crear_audio(duracion + CTA_DUR) # cambia música
        tag = generar_tag_inteligente("oracion", texto, imagen_usada, musica_usada, duracion + CTA_DUR)
        intentos += 1

    # 5) Render final
    render_video(
        fondo=fondo,
        grad=grad,
        titulo_png="titulo.png",
        clips_png=[("bloque.png", 0, duracion)],  # (png, start, dur)
        audio=audio,
        salida=salida,
    )

    # 6) Registrar
    registrar_video_generado(
        archivo_video=salida,
        tipo="oracion",
        musica=musica_usada,
        imagen=imagen_usada,
        tag=tag,
    )

    limpiar_temporales()
    return salida


def generar_salmo_desde_txt(path_txt: str) -> str:
    _asegurar_dirs()

    with open(path_txt, encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_txt))[0]
    salida = f"videos/salmos/{base}.mp4"

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()][:MAX_ESTROFAS]
    duracion = 5 if MODO_TEST else (len(estrofas) * SEGUNDOS_ESTROFA)

    fondo, grad, imagen_usada = crear_fondo(duracion)
    crear_imagen_titulo(base.replace("_", " ").title(), "titulo.png")

    # Render cada estrofa como png (reusamos "estrofa.png" de forma secuencial)
    clips = []
    start = 0
    for e in estrofas:
        crear_imagen_texto(e, "estrofa.png")
        clips.append(("estrofa.png", start, (2 if MODO_TEST else SEGUNDOS_ESTROFA)))
        start += (2 if MODO_TEST else SEGUNDOS_ESTROFA)

    audio, musica_usada = crear_audio(duracion + CTA_DUR)

    tag = generar_tag_inteligente(
        tipo="salmo",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=duracion + CTA_DUR,
    )

    intentos = 0
    while tag_ya_existe(tag) and intentos < 5:
        fondo, grad, imagen_usada = crear_fondo(duracion)
        audio, musica_usada = crear_audio(duracion + CTA_DUR)
        tag = generar_tag_inteligente("salmo", texto, imagen_usada, musica_usada, duracion + CTA_DUR)
        intentos += 1

    render_video(
        fondo=fondo,
        grad=grad,
        titulo_png="titulo.png",
        clips_png=clips,
        audio=audio,
        salida=salida,
    )

    registrar_video_generado(
        archivo_video=salida,
        tipo="salmo",
        musica=musica_usada,
        imagen=imagen_usada,
        tag=tag,
    )

    limpiar_temporales()
    return salida


def main():
    limpiar_imagenes_corruptas()

    # CLI: python -m generator.generar_video solo <archivo_txt> [--test]
    args = sys.argv[1:]

    global MODO_TEST
    if "--test" in args:
        MODO_TEST = True
        args.remove("--test")

    if len(args) < 2 or args[0] != "solo":
        print("Uso:")
        print("  .venv/bin/python -m generator.generar_video solo textos/oraciones/x.txt")
        print("  .venv/bin/python -m generator.generar_video solo textos/salmos/x.txt --test")
        raise SystemExit(1)

    path = args[1].strip()

    if "/salmos/" in path.lower():
        out = generar_salmo_desde_txt(path)
    else:
        out = generar_oracion_desde_txt(path)

    print(f"[GENERATOR] OK → {out}")


if __name__ == "__main__":
    main()
