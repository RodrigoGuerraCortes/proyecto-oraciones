# generator/v3/generator/integrations/descriptions/youtube.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from generator.content.license import leer_licencia_si_existe
from generator.content.description_utils import detectar_contexto_desde_datetime

# Cargar variables del .env
load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

