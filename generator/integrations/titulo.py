import os
import re

# -------------------------------------------------
# Normalización lingüística (determinista)
# -------------------------------------------------

ACCENT_MAP = {
    "oracion": "oración",
    "senor": "señor",
    "senora": "señora",
    "dios": "Dios",
    "jesus": "Jesús",
    "corazon": "corazón",
    "espiritu": "Espíritu",
    "liberacion": "liberación",
    "agradecimiento": "agradecimiento",
}

STOPWORDS = {"para", "de", "del", "y", "en", "por", "a", "el", "la", "los", "las"}

def aplicar_acentos(texto: str) -> str:
    palabras = texto.split()
    out = []
    for p in palabras:
        base = re.sub(r"[^\w]", "", p.lower())
        out.append(ACCENT_MAP.get(base, p))
    return " ".join(out)

def title_case_es(texto: str) -> str:
    palabras = texto.split()
    out = []
    for i, p in enumerate(palabras):
        if i == 0 or p.lower() not in STOPWORDS:
            out.append(p.capitalize())
        else:
            out.append(p.lower())
    return " ".join(out)

# -------------------------------------------------
# Construcción de título editorial
# -------------------------------------------------

def construir_titulo(
    *,
    archivo: str,
    tipo: str,
    duracion: str = "1 minuto",
    emoji: str = "🙏",
) -> str:
    """
    Genera título limpio y consistente a partir del tipo editorial.
    """

    nombre = os.path.basename(archivo)
    nombre = os.path.splitext(nombre)[0]

    # quitar UUID
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]

    texto = nombre.replace("_", " ").strip()
    texto = aplicar_acentos(texto)
    texto = title_case_es(texto)

    # -------------------------------
    # Salmos numerados
    # -------------------------------
    if tipo == "short_salmo":
        m = re.match(r"salmo\s+(\d+)\s+(.*)", texto, re.IGNORECASE)
        if m:
            numero = m.group(1)
            resto = m.group(2)
            return f"Salmo {numero}: {resto} {emoji} - {duracion}"
        return f"{texto} {emoji} - {duracion}"

    # -------------------------------
    # Oraciones (short)
    # -------------------------------
    if tipo == "short_oracion":
        if texto.lower().startswith("oración"):
            return f"{texto} {emoji} - {duracion}"
        return f"Oración {texto} {emoji} - {duracion}"

    # -------------------------------
    # Oraciones guiadas (long)
    # -------------------------------
    if tipo == "long_oracion_guiada":
        if texto.lower().startswith("oración"):
            return f"{texto} {emoji}"
        return f"Oración guiada: {texto} {emoji}"

    # -------------------------------
    # Fallback genérico
    # -------------------------------
    return f"{texto} {emoji}"
