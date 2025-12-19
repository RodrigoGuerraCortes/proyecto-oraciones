# generator/content/description_utils.py

from datetime import time


def detectar_contexto_desde_datetime(dt) -> str:
    """
    Retorna: 'mañana', 'dia' o 'noche'
    """
    hora = dt.time()

    if time(6, 0) <= hora < time(12, 0):
        return "mañana"
    elif time(12, 0) <= hora < time(20, 0):
        return "dia"
    else:
        return "noche"    
