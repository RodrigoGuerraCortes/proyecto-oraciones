# generator/integrations/descriptions/facebook.py

from openai import OpenAI
import os
from dotenv import load_dotenv

from generator.content.description_utils import detectar_contexto_desde_datetime

load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generar_descripcion_facebook(
    *,
    tipo,
    hora_texto,
    archivo_texto=None,
    texto_base=None,
):
    """
    Descripciones optimizadas para Facebook Reels:
    - UNA sola línea
    - Utilidad inmediata
    - Lenguaje cotidiano
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
    # 2) Contexto horario (sutil)
    # -------------------------------------------------
    contexto = detectar_contexto_desde_datetime(hora_texto)
    # mañana / dia / noche

    # -------------------------------------------------
    # 3) Hashtags determinísticos
    # -------------------------------------------------
    if tipo == "oracion":
        hashtags = (
            "#oracion #jesus #catolico #fe #dios "
            "#oraciondiaria #espiritualidad #cristiano"
        )
    else:
        hashtags = (
            "#salmo #biblia #palabradedios #jesus "
            "#fe #dios #espiritualidad #cristiano"
        )

    # -------------------------------------------------
    # 4) Prompt estricto
    # -------------------------------------------------
    base_instrucciones = """
Reglas estrictas:
- UNA sola línea (obligatorio)
- Máximo 8–10 palabras
- 1 emoji máximo
- Lenguaje humano y directo
- Hablar en presente
- Enfocarse en ayuda inmediata

PROHIBIDO:
- Lenguaje poético
- Reflexiones abstractas
- Generalidades espirituales
- “Amén”
- Hashtags
- Palabras como: mensaje, reflexión, bonito
"""

    if contexto == "mañana":
        enfoque = "comenzar el día con calma y fuerza"
    elif contexto == "noche":
        enfoque = "soltar el día y descansar en paz"
    else:
        enfoque = "sentirse acompañado durante el día"

    prompt = f"""
Eres editor católico especializado en Facebook Reels.

Escribe UNA frase clara y útil
que ayude a {enfoque}.

{base_instrucciones}

OBLIGATORIO:
- Usar un verbo de ayuda concreta
  (ej: sostener, calmar, acompañar, aliviar, fortalecer, descansar)

Tipo de contenido: {tipo}

Texto base (solo para entender el tema, NO copiar):
\"\"\"{contenido}\"\"\"
"""

    # -------------------------------------------------
    # 5) Llamada al modelo
    # -------------------------------------------------
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = response.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Dios te acompaña y te da paz hoy 🙏"
            if tipo == "oracion"
            else "La Palabra de Dios fortalece tu día 🙏"
        )

    return f"{frase}\n\n{hashtags}"
