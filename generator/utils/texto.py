

def dividir_en_bloques(texto: str, max_lineas=8):
    lineas = [l for l in texto.splitlines() if l.strip()]
    bloques = []
    for i in range(0, len(lineas), max_lineas):
        bloque_lineas = lineas[i:i + max_lineas]
        bloques.append("\n".join(bloque_lineas))

    if len(bloques) >= 2:
        ult = bloques[-1].strip().lower().rstrip(".")
        if ult in ["amen", "amén"]:
            bloques[-2] += "\nAmén"
            bloques.pop()

    return bloques



def calcular_duracion_bloque(texto: str) -> int:
    n = len([l for l in texto.splitlines() if l.strip()])
    if n <= 7:
        return 20
    elif n <= 12:
        return 28
    else:
        return 35



def normalizar_salmo_titulo(base: str) -> str:
    partes = base.split("_")
    numero = next((p for p in partes if p.isdigit()), None)
    if numero is None:
        numero = "?"

    nombre_raw = (
        base.replace("salmo", "")
            .replace(numero, "")
            .replace("_", " ")
            .strip()
    )
    nombre_raw = (
        nombre_raw.lower()
            .replace("senor", "señor")
            .replace("dios", "Dios")
    )
    nombre = nombre_raw.title()
    return f"Salmo {numero} — {nombre}"