# generator/pipeline.py
import os
from datetime import datetime

from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein

from generator.generar_oracion import generar_oracion
from generator.generar_salmo import generar_salmo


# Parámetros heredados
ANCHO = 1080
ALTO = 1920

# Oraciones
ORACION_LINEAS_MAX = 10
CTA_DUR = 5

# Salmos
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 16






def generar_videos(tipo: str, cantidad: int, modo_test: bool = False):
    """
    Genera N videos del tipo indicado usando el pipeline.
    - tipo: 'oracion' | 'salmo'
    - cantidad: int
    """
    from generator.content.selector import elegir_texto_para

    assert tipo in ("oracion", "salmo"), f"Tipo inválido: {tipo}"

    print(f"[PIPELINE] Generando {cantidad} videos tipo={tipo}")

    for i in range(cantidad):
        path_txt, base = elegir_texto_para(tipo)

        if tipo == "oracion":
            if modo_test:
                salida = f"videos/test/oraciones/{base}.mp4"
            else:
                salida = f"videos/oraciones/{base}.mp4"

            generar_oracion(
                path_in=path_txt,
                path_out=salida,
                modo_test=modo_test
            )
        else:
            if modo_test:
                salida = f"videos/test/salmos/{base}.mp4"
            else:
                salida = f"videos/salmos/{base}.mp4"
            generar_salmo(
                path_in=path_txt,
                path_out=salida,
                modo_test=modo_test
            )

        print(f"[PIPELINE] OK {i+1}/{cantidad} → {salida}")
