# generator/content/selector.py
import os
from logic.text_seleccion import elegir_no_repetido
from historial import cargar_historial, guardar_historial


def elegir_texto_para(tipo: str):
    """
    Elige un archivo .txt no repetido (ventana la maneja tu helper elegir_no_repetido).
    Retorna (ruta_entrada, base_name_sin_ext)
    """
    historial = cargar_historial()

    carpeta = "textos/salmos" if tipo == "salmo" else "textos/oraciones"
    elegido = elegir_no_repetido(carpeta, historial)

    entrada = os.path.join(carpeta, elegido)
    base = elegido.replace(".txt", "")

    # Mantener el control textos_usados (tu lógica original)
    hist_actual = cargar_historial()
    hist_actual["textos_usados"] = historial.get("textos_usados", [])
    guardar_historial(hist_actual)

    return entrada, base
