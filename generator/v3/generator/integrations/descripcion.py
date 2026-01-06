from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from generator.content.license import leer_licencia_si_existe
from generator.content.description_utils import detectar_contexto_desde_datetime
from generator.v3.generator.integrations.prompt_builder import build_prompt




# -------------------------------------------------
# OpenAI setup
# -------------------------------------------------
load_dotenv("config/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------
# Reglas técnicas por plataforma (ESTÁTICAS)
# -------------------------------------------------
PLATFORM_RULES = {
    "youtube": """
- Máximo 2 líneas
- 1 emoji máximo
- Hashtags al final
- No enlaces
""",
    "facebook": """
- Máximo 3 líneas
- Lenguaje cercano
- Emojis moderados
""",
    "instagram": """
- Máximo 3 líneas
- Emojis permitidos
- Hashtags al final
""",
    "tiktok": """
- Frase corta y directa
- Máximo 2 emojis
- Hashtags relevantes
""",
}

# ======================================================
# FUNCIONES AUXILIARES
# ======================================================

def _limpiar_texto_generado(texto: str) -> str:
    # Eliminar hashtags
    texto = re.sub(r"#\w+", "", texto)

    # Eliminar emojis (más agresivo)
    texto = re.sub(
        r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]",
        "",
        texto,
    )

    # Normalizar espacios
    texto = re.sub(r"\s{2,}", " ", texto)

    return texto.strip()


# ======================================================
# API PÚBLICA
# ======================================================

def generar_descripcion(
    *,
    tipo: str,
    plataforma: str,
    publicar_en: datetime,
    texto_base: str,
    editorial_cfg: dict,
    licence: str | None = None,
) -> str:
    """
    Genera descripción FINAL para cualquier plataforma,
    usando SOLO configuración editorial proveniente del canal.
    """

    # ------------------------------
    # Contexto horario
    # ------------------------------
    contexto = detectar_contexto_desde_datetime(publicar_en)

    # ------------------------------
    # Validaciones mínimas
    # ------------------------------
    platform_rules = PLATFORM_RULES.get(plataforma)
    if not platform_rules:
        raise RuntimeError(f"Plataforma no soportada: {plataforma}")

    tipo_cfg = editorial_cfg.get("tipo_cfg", {})
    if not tipo_cfg:
        raise RuntimeError("editorial_cfg.tipo_cfg no definido")

    # ------------------------------
    # Prompt (IA)
    # ------------------------------
    prompt = build_prompt(
        editorial_cfg=editorial_cfg,
        tipo=tipo,
        contexto=contexto,
        platform_rules=platform_rules,
        texto_base=texto_base or "",
    )

    # ------------------------------
    # Llamada al modelo
    # ------------------------------
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        texto_generado = response.choices[0].message.content.strip()

    except Exception:
        # --------------------------
        # Fallback editorial
        # --------------------------
        texto_generado = tipo_cfg.get(
            "fallback",
            "Contenido disponible 🙏"
        )


    texto_generado = _limpiar_texto_generado(texto_generado)

    # ------------------------------
    # Hashtags (editorial)
    # ------------------------------
    hashtags_cfg = tipo_cfg.get("hashtags", {})
    hashtags = (
        hashtags_cfg.get(contexto)
        or hashtags_cfg.get("default")
        or ""
    )

    # ------------------------------
    # Licencia (si existe)
    # ------------------------------
    licencia_texto = leer_licencia_si_existe(licence)
    bloque_licencia = ""

    if licencia_texto:
        bloque_licencia = (
            "\n\n──────────────\n"
            "🎵 Música:\n"
            f"{licencia_texto}"
        )

    # ------------------------------
    # Resultado final
    # ------------------------------
    return f"{texto_generado}\n\n{hashtags}{bloque_licencia}"
