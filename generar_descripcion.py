from openai import OpenAI
import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==========================================================
#  DESCRIPCIÓN PROFESIONAL, VIRAL Y SUPER OPTIMIZADA
# ==========================================================
def generar_descripcion(tipo, hora_texto, archivo_texto):
    """
    Genera una descripción ULTRA CORTA y PROFESIONAL para YouTube/Facebook.
    Estilo viral, 2–3 líneas, sin Amén, con hashtags forzados por tipo/momento.
    """

    # 1) Leer texto original SOLO para inspiración
    try:
        with open(archivo_texto, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
    except:
        contenido = ""

    # 2) Detectar momento del día
    if hora_texto == "05:00":
        contexto = "mañana"
    elif hora_texto == "19:00":
        contexto = "noche"
    else:
        contexto = "dia"

    # ======================================================
    # 3) Hashtags VIRALIZADOS FORZADOS por tipo + momento
    # ======================================================

    if tipo == "oracion" and contexto == "mañana":
        hashtags_finales = "#oracionDelDia #fe #jesus #catolico #bendicion #espiritualidad #dios"
    elif tipo == "oracion" and contexto == "noche":
        hashtags_finales = "#oracionDeNoche #fe #jesus #catolico #pazInterior #descanso #dios"
    elif tipo == "oracion":
        hashtags_finales = "#oracion #fe #jesus #catolico #espiritualidad #bendicion #dios"
    else:  # SALMOS
        hashtags_finales = "#salmo #biblia #fe #jesus #catolico #espiritualidad #dios"

    # ======================================================
    # 4) Prompt optimizado estilo viral
    # ======================================================
    prompt = f"""
Genera una descripción ULTRA CORTA y profesional para un video católico de 1 minuto.

Reglas obligatorias:
- Solo 2 o 3 líneas.
- NO escribas párrafos largos.
- NO incluyas "Amén".
- Usa tono cálido y viral (como páginas grandes de oración).
- NO expliques ni reescribas la oración completa.
- Máximo 1 o 2 emojis.
- NO incluyas hashtags (yo los agregaré después).
- Solo escribe la parte del texto, NO incluyas hashtags.

Tipo: {tipo}
Momento del día: {contexto}

Texto base (solo inspiración, NO lo reescribas):
\"\"\"{contenido}\"\"\"

Ejemplos del estilo exacto que quiero:

- "Una oración para comenzar tu día con paz 🙏✨
Que la bendición de Dios ilumine tu hogar."

- "Una oración para descansar en Su paz 🌙🙏
Que Dios cuide tu descanso esta noche."

- "Un salmo para fortalecer tu espíritu 🙏
Que la Palabra de Dios ilumine tu vida hoy."

Genera AHORA una descripción en este estilo.
"""

    # ======================================================
    # 5) Llamado a la IA
    # ======================================================
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        texto_corto = response.choices[0].message.content.strip()

    except Exception as e:
        print("[IA Error - usando fallback]", e)

        # Fallback según tipo + contexto
        if tipo == "oracion" and contexto == "mañana":
            texto_corto = "Una oración para comenzar tu día con paz 🙏✨\nQue Dios bendiga tu caminar hoy."
        elif tipo == "oracion" and contexto == "noche":
            texto_corto = "Una oración para descansar en la paz de Dios 🌙🙏\nQue Él cuide tu descanso esta noche."
        elif tipo == "oracion":
            texto_corto = "Una oración para acompañarte hoy 🙏\nQue Dios ilumine tu vida."
        else:
            texto_corto = "Un salmo para fortalecer tu espíritu 🙏✨\nQue la Palabra de Dios te guíe hoy."

    # ======================================================
    # 6) ENSAMBLAR descripción final + hashtags forzados
    # ======================================================
    descripcion_final = f"{texto_corto}\n\n{hashtags_finales}"

    return descripcion_final


# ==========================================================
#  CONVERSIÓN A TAGS PARA YOUTUBE (opcional)
# ==========================================================
def generar_tags_from_descripcion(descripcion):
    """
    Extrae los hashtags del texto final y los transforma en tags de YouTube.
    """
    palabras = descripcion.split()
    hashtags = [p for p in palabras if p.startswith("#")]

    # limpiar #
    tags = [h[1:] for h in hashtags]

    # evitar duplicados conservando orden
    tags_unicos = list(dict.fromkeys(tags))

    return tags_unicos
