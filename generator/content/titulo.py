# generator/content/titulo.py

import os
import re

# Reemplazos básicos de acentos frecuentes (seguro, determinista)
ACCENT_MAP = {
    "oracion": "oración",
    "senor": "señor",
    "senora": "señora",
    "dios": "Dios",
    "jesus": "Jesús",
    "corazon": "corazón",
    "espiritu": "espíritu",
    "misericordia": "misericordia",
    "liberacion": "liberación",
    "agradecimiento": "agradecimiento",
}

def aplicar_acentos(texto: str) -> str:
    palabras = texto.split()
    out = []
    for p in palabras:
        base = re.sub(r"[^\w]", "", p.lower())
        if base in ACCENT_MAP:
            out.append(ACCENT_MAP[base])
        else:
            out.append(p)
    return " ".join(out)

def title_case_es(texto: str) -> str:
    # Capitaliza palabras relevantes, deja preposiciones en minúscula
    stopwords = {"para", "de", "del", "y", "en", "por", "a", "el", "la", "los", "las"}
    palabras = texto.split()
    out = []
    for i, p in enumerate(palabras):
        if i == 0 or p.lower() not in stopwords:
            out.append(p.capitalize())
        else:
            out.append(p.lower())
    return " ".join(out)

def construir_titulo_desde_archivo(archivo: str) -> str:
    nombre = os.path.basename(archivo)
    nombre = os.path.splitext(nombre)[0]

    # quitar UUID
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]

    texto = nombre.replace("_", " ").strip()

    # detectar salmo con número
    m = re.match(r"salmo\s+(\d+)\s+(.*)", texto, re.IGNORECASE)
    if m:
        numero = m.group(1)
        resto = m.group(2)
        resto = aplicar_acentos(resto)
        resto = title_case_es(resto)
        return f"Salmo {numero}: {resto} 🙏 - 1 minuto"

    # oraciones u otros
    texto = aplicar_acentos(texto)
    texto = title_case_es(texto)

    # prefijo elegante
    if texto.lower().startswith("oración"):
        return f"{texto} 🙏 - 1 minuto"

    return f"{texto} 🙏 - 1 minuto"
