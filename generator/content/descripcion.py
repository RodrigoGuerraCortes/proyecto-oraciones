# generator/content/descripcion.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from generator.content.license import leer_licencia_si_existe

# Cargar variables del .env
load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def seleccionar_estilo_prompt(publication_id: int) -> int:
    return publication_id % 3

# =====================================================================
#   FUNCIÓN PRINCIPAL — AHORA MULTIPLATAFORMA
# =====================================================================
def generar_descripcion(
    *,
    tipo,
    hora_texto,
    plataforma="youtube",
    archivo_texto=None,
    texto_base=None,
    licence=None,
):

    """
    Genera una descripción optimizada según plataforma:
        - "youtube"
        - "facebook"
        - "instagram"
    """

    if plataforma == "youtube":
        return generar_descripcion_youtube(
                tipo=tipo,
                hora_texto=hora_texto,
                archivo_texto=archivo_texto,
                texto_base=texto_base,
                licence=licence,
            )
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

def generar_descripcion_youtube(
    *,
    tipo,
    hora_texto,
    archivo_texto=None,
    texto_base=None,
    licence=None,
):
    """
    Genera descripciones profesionales, únicas y estables
    optimizadas para YouTube Shorts, según contexto horario.
    """

    # -------------------------------------------------
    # 1) Contenido base (SOLO referencia semántica)
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
    # 2) Detectar contexto horario
    # -------------------------------------------------
    contexto = detectar_contexto_desde_datetime(hora_texto)
    # valores: "mañana", "dia", "noche"

    # -------------------------------------------------
    # 3) Hashtags por tipo + contexto
    # -------------------------------------------------
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
    else:  # salmos
        hashtags_finales = (
            "#salmo #biblia #palabraDeDios #jesus #catolico "
            "#espiritualidad #fe #salmododia #dios"
        )

    # -------------------------------------------------
    # 4) Prompt por contexto (CON anclaje semántico)
    # -------------------------------------------------
    base_instrucciones = """
Reglas estrictas:
- NO resumir ni reescribir el texto base
- NO citar frases del texto
- La descripción debe estar relacionada con el TEMA CENTRAL,
  no con el contenido literal
- Máximo 2 líneas
- 1 emoji máximo
- Lenguaje humano y cercano
- NO clichés
- NO promoción
- NO “Amén”
"""

    if contexto == "mañana":
        prompt = f"""
Eres editor católico para YouTube Shorts.

Escribe una descripción serena y esperanzadora
para comenzar el día con Dios.
Debe acompañar, no enseñar.

{base_instrucciones}

Texto base (solo para entender el tema):
\"\"\"{contenido}\"\"\"
"""

    elif contexto == "noche":
        prompt = f"""
Eres comunicador católico para la noche.

Redacta una descripción íntima y de descanso,
que ayude a cerrar el día en paz y confianza.

{base_instrucciones}

Texto base (solo para entender el tema):
\"\"\"{contenido}\"\"\"
"""

    else:  # día
        prompt = f"""
Eres especialista en mensajes católicos cotidianos.

Escribe una descripción clara y útil,
que acompañe al espectador durante el día.

{base_instrucciones}

Texto base (solo para entender el tema):
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
        texto_corto = response.choices[0].message.content.strip()

    except Exception:
        texto_corto = (
            "Que Dios acompañe cada paso de tu día 🙏"
            if tipo == "oracion"
            else "Que la Palabra de Dios fortalezca tu camino 🙏"
        )

    # -------------------------------------------------
    # 6) Bloque de licencia (si existe)
    # -------------------------------------------------
    licencia_texto = leer_licencia_si_existe(licence)

    if licencia_texto:
        bloque_licencia = (
            "\n\n──────────────\n"
            "🎵 Música:\n"
            f"{licencia_texto}"
        )
        return f"{texto_corto}\n\n{hashtags_finales}{bloque_licencia}"

    return f"{texto_corto}\n\n{hashtags_finales}"



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
Eres experto en contenido católico optimizado para **Facebook Reels**.

Genera **UNA sola línea**, máximo 8–10 palabras.
1 emoji permitido.

La frase DEBE:
- Expresar ayuda inmediata (no reflexión)
- Indicar para qué sirve el video
- Sonar humana, cotidiana y directa
- Invitar a quedarse viendo

OBLIGATORIO:
- Usar UN verbo de ayuda concreta (ej: sostener, calmar, acompañar, aliviar, descansar, fortalecer)
- Hablar en presente

PROHIBIDO:
- Frases que comiencen con “Cuando sientes…”
- Lenguaje poético o abstracto
- Generalidades espirituales
- “Amén”
- Hashtags
- Palabras como “mensaje”, “reflexión”, “bonito”

Tipo de contenido: {tipo}

Texto base (solo contexto, no copiar):
\"\"\"{contenido}\"\"\"

Genera UNA línea clara, útil y humana.
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
    hashtags = "#oracion #jesus #catolico #fe #dios #cristiano #espiritualidad"

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

Texto base (solo inspiración):
\"\"\"{contenido}\"\"\"
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



def detectar_contexto_desde_datetime(dt) -> str:
    """
    Retorna: mañana | dia | noche
    """
    hora = dt.hour

    if 6 <= hora < 12:
        return "mañana"
    elif 12 <= hora < 19:
        return "dia"
    else:
        return "noche"
