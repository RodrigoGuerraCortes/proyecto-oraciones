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
    Genera descripciones profesionales, únicas, optimizadas para YouTube
    sin repetir frases y adaptadas al tema del salmo/oración.
    """

    # 1) Leer contenido base
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
    # 3) Hashtags MEJORADOS profesionalmente (SEO real)
    # ======================================================
    if tipo == "oracion" and contexto == "mañana":
        hashtags_finales = (
            "#oracionDelDia #oraciondeLaManana #jesus #fe #catolico "
            "#bendicion #espiritualidad #dios"
        )

    elif tipo == "oracion" and contexto == "noche":
        hashtags_finales = (
            "#oracionDeNoche #descansoconDios #fe #jesus #catolico "
            "#pazInterior #espiritualidad #dios"
        )

    elif tipo == "oracion":
        hashtags_finales = (
            "#oracion #jesus #catolico #fe #bendicion "
            "#espiritualidad #poderDeLaOracion #dios"
        )

    else:  # SALMOS
        hashtags_finales = (
            "#salmo #biblia #palabraDeDios #jesus #catolico "
            "#espiritualidad #fe #salmododia #dios"
        )

    # ======================================================
    # 4) Nuevo prompt mejorado (mucho más profesional)
    # ======================================================
    prompt = f"""
Eres un experto en comunicación católica viral para YouTube.

Necesito que generes **una descripción ULTRA CORTA y ÚNICA**, máximo 2–3 líneas,
para un video de 1 minuto.

REGLAS OBLIGATORIAS:
- NO reescribas ni resumas el texto original.
- NO uses frases genéricas como “Un salmo para llenar tu día de esperanza”.
- NO repitas frases usadas anteriormente.
- Detecta el **tema central** del texto (ej: confianza, esperanza, protección, gratitud, sabiduría, fortaleza).
- Genera una descripción completamente **nueva y fresca** basada en ese tema.
- Tono cálido, espiritual, emotivo y viral (estilo contenido católico grande).
- Máximo 1 o 2 emojis.
- NO incluyas hashtags.
- NO incluyas “Amén”.

DATOS:
- Tipo: {tipo}
- Momento del día: {contexto}

TEXTO BASE (solo inspiración):
\"\"\"{contenido}\"\"\"

Ejemplos del estilo deseado:
- "Un mensaje para renovar tu confianza en Dios 🙏✨  
Que Su presencia te fortalezca hoy."

- "Una invitación a descansar en la paz del Señor 🌙✨  
Que Él calme tu corazón en este momento."

Ahora genera **una nueva descripción única y profesional**.
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

        # fallback según tipo
        if tipo == "salmo":
            texto_corto = "Un salmo para fortalecer tu espíritu 🙏✨\nQue la Palabra de Dios ilumine tu vida."
        else:
            texto_corto = "Una oración para acompañarte hoy 🙏✨\nQue Dios bendiga tu camino."

    # ======================================================
    # 6) Unir descripción + hashtags
    # ======================================================
    return f"{texto_corto}\n\n{hashtags_finales}"



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
