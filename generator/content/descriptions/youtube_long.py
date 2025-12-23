# generator/content/descriptions/youtube_long.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from generator.content.license import leer_licencia_si_existe

# -------------------------------------------------
# Configuración
# -------------------------------------------------
load_dotenv("config/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================================
#   YOUTUBE — DESCRIPCIÓN PARA VIDEOS LONG (3–5 min)
# =====================================================================

def generar_descripcion_youtube_long(
    *,
    hora_texto,
    texto_base=None,
    licence=None,
):
    """
    Genera una descripción contemplativa y estable
    para videos LONG de oración guiada en YouTube.

    Reglas editoriales:
    - NO dependiente del horario
    - Ritmo pausado
    - Invita a permanecer
    - Optimizada para retención y sesión
    """

    # -------------------------------------------------
    # 1️⃣ Contenido base (solo referencia semántica)
    # -------------------------------------------------
    contenido = (texto_base or "").strip()

    # -------------------------------------------------
    # 2️⃣ Instrucciones editoriales
    # -------------------------------------------------
    prompt = f"""
Eres editor católico especializado en videos largos
de oración guiada para YouTube (3–5 minutos).

Objetivo:
- Invitar al espectador a quedarse
- Crear un espacio de calma y recogimiento
- Acompañar en silencio y reflexión

Reglas estrictas:
- NO resumir ni reescribir el texto base
- NO citar frases del texto
- NO enseñar ni explicar
- NO clichés
- NO promoción
- NO llamado a suscribirse
- NO “Amén”
- Máximo 4 líneas
- Máximo 1 emoji (opcional)
- Lenguaje humano, sereno y profundo

Texto base (solo para comprender el tema):
\"\"\"{contenido}\"\"\"
"""

    # -------------------------------------------------
    # 3️⃣ Llamada al modelo
    # -------------------------------------------------
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        descripcion_principal = response.choices[0].message.content.strip()

    except Exception:
        descripcion_principal = (
            "Un momento de oración guiada para detenerte, respirar "
            "y dejar que Dios hable al corazón 🙏"
        )

    # -------------------------------------------------
    # 4️⃣ Hashtags LONG (menos, más contextuales)
    # -------------------------------------------------
    hashtags = (
        "#oracionGuiada #oracionCatolica "
        "#vidaEspiritual #fe #dios"
    )

    # -------------------------------------------------
    # 5️⃣ Bloque de licencia (si existe)
    # -------------------------------------------------
    licencia_texto = leer_licencia_si_existe(licence)

    if licencia_texto:
        bloque_licencia = (
            "\n\n──────────────\n"
            "🎵 Música:\n"
            f"{licencia_texto}"
        )
        return f"{descripcion_principal}\n\n{hashtags}{bloque_licencia}"

    return f"{descripcion_principal}\n\n{hashtags}"
