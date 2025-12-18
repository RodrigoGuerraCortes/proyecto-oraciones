# generator/oso.py
from generator.pipeline import generar_videos

def generar_oso(ciclos: int, modo_test: bool = False):
    """
    Genera contenido en patrón OSO:
    - Por cada ciclo: Oración, Salmo, Oración
    """
    for i in range(ciclos):
        print(f"[OSO] Ciclo {i+1}/{ciclos} → Oración")
        generar_videos("oracion", 1, modo_test)

        print(f"[OSO] Ciclo {i+1}/{ciclos} → Salmo")
        generar_videos("salmo", 1, modo_test)

        print(f"[OSO] Ciclo {i+1}/{ciclos} → Oración")
        generar_videos("oracion", 1, modo_test)
