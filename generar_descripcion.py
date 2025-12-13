from openai import OpenAI
import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================================
#   FUNCIÓN PRINCIPAL — AHORA MULTIPLATAFORMA
# =====================================================================
def generar_descripcion(tipo, hora_texto, archivo_texto, plataforma="youtube", licence=None):
    """
    Genera una descripción optimizada según plataforma:
        - "youtube"
        - "facebook"
        - "instagram"
    """

    if plataforma == "youtube":
        return generar_descripcion_youtube(tipo, hora_texto, archivo_texto, licence)

    elif plataforma == "facebook":
        return generar_descripcion_facebook(tipo, hora_texto, archivo_texto)
    elif plataforma == "instagram":
        return generar_descripcion_instagram(tipo, hora_texto, archivo_texto)
    elif plataforma == "tiktok":
        return generar_descripcion_tiktok(tipo, hora_texto, archivo_texto)

    else:
        raise ValueError(f"Plataforma no soportada: {plataforma}")


# =====================================================================
#   YOUTUBE — TU VERSIÓN ORIGINAL (sin alterar)
# =====================================================================
def generar_descripcion_youtube(tipo, hora_texto, archivo_texto, licence):
    """
    Genera descripciones profesionales, únicas, optimizadas para YouTube.
    """

    # 1) Leer contenido base
    try:
        with open(archivo_texto, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
    except:
        contenido = ""

    # 2) Detectar momento del día
    if hora_texto == "10:00":
        contexto = "mañana"
    elif hora_texto == "23:10":
        contexto = "noche"
    else:
        contexto = "dia"

    # Hashtags optimizados
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
    else:  # Salmos
        hashtags_finales = (
            "#salmo #biblia #palabraDeDios #jesus #catolico "
            "#espiritualidad #fe #salmododia #dios"
        )

    # Prompt profesional
    prompt = f"""
Eres un experto en comunicación católica viral para YouTube.

Necesito que generes **una descripción ULTRA CORTA y ÚNICA**, máximo 2–3 líneas,
para un video de 1 minuto.

REGLAS OBLIGATORIAS:
- NO reescribas ni resumas el texto original.
- NO uses frases genéricas como “Un salmo para llenar tu día de esperanza”.
- NO repitas frases usadas anteriormente.
- Máximo 1 o 2 emojis.
- NO incluyas hashtags.
- NO incluyas “Amén”.

Datos:
- Tipo: {tipo}
- Momento del día: {contexto}

Texto base:
\"\"\"{contenido}\"\"\"

Genera una descripción única.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        texto_corto = response.choices[0].message.content.strip()

    except Exception:
        # Fallback básico
        texto_corto = (
            "Un mensaje breve para acompañar tu día 🙏✨"
            if tipo == "oracion"
            else "Un salmo para fortalecer tu espíritu 🙏✨"
        )


    licencia_texto = leer_licencia_si_existe(licence)

    
    if licencia_texto:
        bloque_licencia = (
            "\n\n──────────────\n"
            "🎵 Música:\n"
            f"{licencia_texto}"
        )

    return f"{texto_corto}\n\n{hashtags_finales}{bloque_licencia}"


# =====================================================================
#   FACEBOOK — DESCRIPCIÓN ULTRA CORTA + HASHTAGS POTENTES
# =====================================================================
def generar_descripcion_facebook(tipo, hora_texto, archivo_texto):
    """
    Genera descripciones optimizadas para Facebook Reels:
        - Ultra cortas (1 línea)
        - Más emocionales
        - Con hashtags optimizados al final
    """

    # Leer contenido como inspiración
    try:
        with open(archivo_texto, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
    except:
        contenido = ""

    prompt = f"""
Eres experto en contenido católico viral para **Facebook Reels**.

Necesito que generes **UNA sola línea**, máximo 10–12 palabras,
muy emocional, muy directa y con 1 emoji permitido.

Reglas:
- NO resumas ni reescribas el texto original.
- NO uses frases genéricas (“hermoso mensaje”, “bonitas palabras”).
- NO repitas frases existentes.
- NO agregues hashtags.
- NO digas “Amén”.
- Debe sonar humano, cálido y ESPIRITUAL.

Datos:
- Tipo de contenido: {tipo}

Texto base (solo inspiración):
\"\"\"{contenido}\"\"\"

Genera SOLO UNA línea emocional.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = resp.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Que la paz de Dios toque tu corazón hoy 🙏✨"
            if tipo == "oracion"
            else "Que la Palabra de Dios fortalezca tu vida 🙏✨"
        )

    # Hashtags optimizados para viralidad en Reels
    hashtags = "#oracion #jesus #catolico #fe #amen #dios #cristiano #espiritualidad"

    return f"{frase}\n\n{hashtags}"


# =====================================================================
#   INSTAGRAM — DESCRIPCIÓN EMOCIONAL + HASHTAGS CORTOS
# =====================================================================
def generar_descripcion_instagram(tipo, hora_texto, archivo_texto):

    # Leer el archivo como inspiración
    try:
        with open(archivo_texto, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
    except:
        contenido = ""

    prompt = f"""
Eres experto en contenido viral católico para **Instagram Reels**.

Necesito que generes:
- UNA sola frase (máximo 10–12 palabras)
- Muy emocional y espiritual
- 1 o 2 emojis permitidos
- NO resumas el texto original
- NO repitas frases comunes
- NO escribas “Amén”
- NO incluyas hashtags en la frase
- Debe sonar íntima y profunda
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = resp.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Que Dios ilumine tu corazón hoy 🙏✨"
            if tipo == "oracion"
            else "Que su Palabra renueve tu espíritu 🙏✨"
        )

    # Hashtags especiales para Instagram (mejor performance con 3–4)
    hashtags = "#fe #dios #oracion #catolico"

    return f"{frase}\n\n{hashtags}"


# =====================================================================
#   TIKTOK — FRASE DIRECTA + HASHTAGS DE DESCUBRIMIENTO
# =====================================================================
def generar_descripcion_tiktok(tipo, hora_texto, archivo_texto):

    # Leer contenido solo como inspiración
    try:
        with open(archivo_texto, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
    except:
        contenido = ""

    prompt = f"""
Eres experto en contenido católico viral para **TikTok**.

Necesito que generes:
- UNA frase corta (máx. 8–10 palabras)
- Muy emocional y espiritual
- Lenguaje sencillo y humano
- 1 o 2 emojis permitidos
- NO resumas ni reescribas el texto
- NO frases genéricas
- NO escribas “Amén”
- NO incluyas hashtags en la frase
- Debe funcionar para TikTok (hook rápido)
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        frase = resp.choices[0].message.content.strip()

    except Exception:
        frase = (
            "Pon a Dios en el centro de tu día 🙏✨"
            if tipo == "oracion"
            else "La Palabra de Dios transforma el corazón 🙏✨"
        )

    # Hashtags más amplios para TikTok (descubrimiento)
    if tipo == "oracion":
        hashtags = (
            "#oracion #oraciondiaria #dios #fe #jesus "
        )
    else:
        hashtags = (
            "#salmo #biblia #palabradedios #fe #jesus "
        )

    return f"{frase}\n\n{hashtags}"




# =====================================================================
#   TAGS (solo usados en YouTube)
# =====================================================================
def generar_tags_from_descripcion(descripcion):
    """
    Extrae hashtags → los transforma en tags de YouTube.
    """
    palabras = descripcion.split()
    hashtags = [p for p in palabras if p.startswith("#")]
    tags = [h[1:] for h in hashtags]

    # Sin duplicados
    return list(dict.fromkeys(tags))

# =====================================================================
#   Licence para youtube
# =====================================================================
def leer_licencia_si_existe(path):
    if not path:
        return ""

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""

    return ""