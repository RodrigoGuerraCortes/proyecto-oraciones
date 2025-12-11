import os
import random
from datetime import datetime, timedelta


def elegir_no_repetido(carpeta, historial, dias_no_repetir=7):
    """
    Elige un archivo de texto NO usado recientemente,
    NO usado en pendientes,
    y NO usado en publicados.
    """

    hoy = datetime.now()
    limite = hoy - timedelta(days=dias_no_repetir)

    # --------------------------------------------------------------------
    # 1) Mantener textos_usados limpio (últimos N días)
    # --------------------------------------------------------------------
    if carpeta not in historial["textos_usados"]:
        historial["textos_usados"][carpeta] = []

    recientes = []
    for item in historial["textos_usados"][carpeta]:
        try:
            fecha = datetime.fromisoformat(item["fecha"])
            if fecha > limite:
                recientes.append(item)
        except:
            pass

    historial["textos_usados"][carpeta] = recientes

    usados_nombres = {item["nombre"] for item in recientes}

    # --------------------------------------------------------------------
    # 2) Obtener nombre base de textos en pendientes + publicados
    # --------------------------------------------------------------------
    ocupados = set()

    for grupo in ("pendientes", "publicados"):
        for item in historial.get(grupo, []):
            archivo = item.get("archivo")  # ejemplo: videos/oraciones/oracion_x.mp4
            if not archivo:
                continue

            base = os.path.splitext(os.path.basename(archivo))[0]
            ocupados.add(base)

    # --------------------------------------------------------------------
    # 3) Archivos reales de la carpeta
    # --------------------------------------------------------------------
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]

    archivos_base = [a.replace(".txt", "") for a in archivos]

    # --------------------------------------------------------------------
    # 4) Filtrar todos los que NO se pueden usar
    # --------------------------------------------------------------------
    disponibles = [
        base for base in archivos_base
        if base not in usados_nombres
        and base not in ocupados
    ]

    # Si no queda ninguno: reset de usados, pero NO de pendientes ni publicados
    if not disponibles:
        disponibles = [
            base for base in archivos_base
            if base not in ocupados
        ]
        historial["textos_usados"][carpeta] = []

    elegido = random.choice(disponibles)
    historial["textos_usados"][carpeta].append({
        "nombre": elegido,
        "fecha": hoy.isoformat()
    })

    return elegido + ".txt"
