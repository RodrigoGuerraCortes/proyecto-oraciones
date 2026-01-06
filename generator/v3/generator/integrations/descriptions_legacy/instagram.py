# generator/v3/generator/integrations/descriptions/facebook.py

from openai import OpenAI
import os
from dotenv import load_dotenv

from generator.content.description_utils import detectar_contexto_desde_datetime

load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generar_descripcion_instagram(
    *,
    tipo,
    hora_texto,
    archivo_texto=None,
    texto_base=None,
):
    """
    Descripciones optimizadas para Instagram Reels:
    - UNA sola frase
    - Emocional e íntima
    - Con ayuda emocional clara
    """

    # -------------------------------------------------
    # 1) Contenido base (anclaje semántico)
    # -------------------------------------------------
    if texto_base:
        contenido = texto_base.strip()
    elif archivo_texto:
        try:
            with open(archivo_texto, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
        except Exception:
            contenido = ""
    else:
        contenido = ""

    # -------------------------------------------------
    # 2) Contexto horario (sutil, emocional)
    # -------------------------------------------------
    contexto = detectar_contexto_desde_datetime(hora_texto)
    # mañana / dia / noche

    if contexto == "mañana":
        enfoque = "comenzar el día con esperanza"
    elif contexto == "noche":
        enfoque = "descansar y soltar el día"
    else:
        enfoque = "sentirse acompañado ahora"

    # -------------------------------------------------
    # 3) Prompt editorial (más disciplinado)
    # -------------------------------------------------
    base_instrucciones = """
Reglas estrictas:
- UNA sola frase
- Máximo 10–12 palabras
- Lenguaje simple, humano e íntimo
- 1 o 2 emojis máximo
- Hablar en presente

OBLIGATORIO:
- Usar un verbo activo de experiencia interior
  (ej: sentir, descansar, confiar, sanar, entregar, sostener)
- Ayudar emocionalmente al espectador

PROHIBIDO:
- Lenguaje poético abstracto
- Frases genéricas espirituales
- “Amén”
- Hashtags en la frase
"""

    prompt = f"""
Eres editor de contenido católico para Instagram Reels.

Escribe UNA frase emocional e íntima
que ayude a {enfoque}.

{base_instrucciones}

Tipo de contenido: {tipo}

Texto base (solo inspiración, NO copiar):
\"\"\"{contenido}\"\"\"
"""

    # -------------------------------------------------
    # 4) Llamada al modelo
    # -------------------------------------------------
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = response.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Descansa en Dios y siente Su paz hoy 🙏✨"
            if tipo == "oracion"
            else "La Palabra de Dios renueva tu interior hoy 🙏✨"
        )

    # -------------------------------------------------
    # 5) Hashtags (cortos, pero con intención)
    # -------------------------------------------------
    if tipo == "oracion":
        hashtags = "#fe #oracion #jesus #catolico"
    else:
        hashtags = "#fe #biblia #jesus #catolico"

    return f"{frase}\n\n{hashtags}"
