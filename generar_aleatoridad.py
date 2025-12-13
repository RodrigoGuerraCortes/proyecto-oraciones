import os
import random

# memoria local por ejecución
_IMAGENES_USADAS_EN_ESTA_EJECUCION = set()


def elegir_imagen_no_reciente(historial, carpeta="imagenes", ventana=10):
    """
    Elige una imagen evitando:
    - Las usadas en los últimos N videos (historial)
    - Las usadas en esta misma ejecución (batch)
    """

    todas = [
        i for i in os.listdir(carpeta)
        if i.lower() != "vignette.png"
    ]

    # Últimas imágenes del historial
    usadas_historial = [
        v.get("imagen")
        for v in historial.get("publicados", [])[-ventana:]
        if v.get("imagen")
    ]

    # Pool limpio
    candidatas = [
        i for i in todas
        if i not in usadas_historial
        and i not in _IMAGENES_USADAS_EN_ESTA_EJECUCION
    ]

    # Si se agotó el pool, relajamos reglas
    if not candidatas:
        candidatas = [
            i for i in todas
            if i not in _IMAGENES_USADAS_EN_ESTA_EJECUCION
        ]

    # Si aún no hay, ya no queda opción
    if not candidatas:
        candidatas = todas

    elegida = random.choice(candidatas)
    _IMAGENES_USADAS_EN_ESTA_EJECUCION.add(elegida)

    return elegida



_MUSICAS_USADAS_EN_ESTA_EJECUCION = set()

def elegir_musica_no_reciente(historial, carpeta="musica", ventana=12):
    todas = [
        f for f in os.listdir(carpeta)
        if f.lower().endswith(".mp3")
    ]

    usadas_historial = [
        v.get("musica")
        for v in historial.get("publicados", [])[-ventana:]
        if v.get("musica")
    ]

    candidatas = [
        m for m in todas
        if m not in usadas_historial
        and m not in _MUSICAS_USADAS_EN_ESTA_EJECUCION
    ]

    if not candidatas:
        candidatas = [
            m for m in todas
            if m not in _MUSICAS_USADAS_EN_ESTA_EJECUCION
        ]

    if not candidatas:
        candidatas = todas

    elegida = random.choice(candidatas)
    _MUSICAS_USADAS_EN_ESTA_EJECUCION.add(elegida)

    return elegida
