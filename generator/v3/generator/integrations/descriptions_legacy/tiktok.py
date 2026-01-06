# generator/v3/generator/integrations/descriptions/tiktok.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from generator.content.description_utils import detectar_contexto_desde_datetime

# Cargar variables del .env
load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================================================================
#   TIKTOK — HOOK DIRECTO + DESCUBRIMIENTO
# =====================================================================
def generar_descripcion_tiktok(
    *,
    tipo,
    hora_texto,
    archivo_texto=None,
    texto_base=None,
):
    """
    Descripción optimizada para TikTok:
    - Hook inmediato
    - Utilidad emocional clara
    - Lenguaje simple y humano
    """

    # -------------------------------------------------
    # 1) Contenido base (solo anclaje semántico)
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
    # 2) Contexto horario (sutil pero útil)
    # -------------------------------------------------
    contexto = detectar_contexto_desde_datetime(hora_texto)
    # mañana / dia / noche

    if contexto == "mañana":
        momento = "comenzar el día"
    elif contexto == "noche":
        momento = "cerrar el día"
    else:
        momento = "seguir adelante hoy"

    # -------------------------------------------------
    # 3) Prompt editorial (estricto)
    # -------------------------------------------------
    prompt = f"""
Eres editor de contenido católico especializado en **TikTok**.

Escribe UNA sola frase que sirva como HOOK inmediato.

Reglas estrictas:
- Máximo 8–10 palabras
- Lenguaje simple y humano
- Muy emocional pero concreta
- 1 emoji máximo
- Debe ayudar a {momento}
- Hablar en presente

OBLIGATORIO:
- Usar un verbo de acción interior
  (ej: confiar, soltar, descansar, sostener, sanar, entregar)

PROHIBIDO:
- Lenguaje poético abstracto
- Frases genéricas espirituales
- “Amén”
- Hashtags en la frase
- Promesas exageradas

Tipo de contenido: {tipo}

Texto base (solo para entender el tema, NO copiar):
\"\"\"{contenido}\"\"\"
"""

    # -------------------------------------------------
    # 4) Llamada al modelo
    # -------------------------------------------------
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = resp.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Hoy suelto mis cargas y confío en Dios 🙏"
            if tipo == "oracion"
            else "La Palabra de Dios sostiene mi camino 🙏"
        )

    # -------------------------------------------------
    # 5) Hashtags de descubrimiento (TikTok)
    # -------------------------------------------------
    if tipo == "oracion":
        hashtags = (
            "#oracion #oraciondiaria #fe #dios #jesus"
        )
    else:
        hashtags = (
            "#salmo #biblia #palabradedios #fe #jesus"
        )

    return f"{frase}\n\n{hashtags}"
