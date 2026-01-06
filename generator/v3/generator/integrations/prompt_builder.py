# generator/v3/generator/integrations/prompt_builder.py

def build_prompt(
    *,
    editorial_cfg: dict,
    tipo: str,
    contexto: str,
    platform_rules: str,
    texto_base: str,
) -> str:
    """
    Construye el prompt FINAL para el modelo.

    - editorial_cfg: configuración editorial del canal
    - tipo: short_oracion | short_salmo | long_oracion_guiada | etc.
    - contexto: mañana | dia | noche
    - platform_rules: restricciones técnicas
    - texto_base: SOLO referencia semántica (no copiar)
    """

    tipo_cfg = editorial_cfg.get("tipo_cfg", {})

    # ------------------------------
    # Tono editorial
    # ------------------------------
    tone_cfg = tipo_cfg.get("tone", {})
    tono = (
        tone_cfg.get(contexto)
        or tone_cfg.get("default")
        or "cercano, humano y respetuoso"
    )

    prompt = f"""
Eres redactor profesional de contenido digital.

Tono general:
{tono}

Restricciones técnicas de la plataforma:
{platform_rules}

Texto base (SOLO para entender el tema, NO citar ni resumir):
\"\"\"{texto_base}\"\"\"

Instrucciones estrictas:
- NO incluyas emojis
- NO incluyas hashtags
- NO copies frases del texto base
- NO expliques el contenido
- NO enseñes ni sermonees
- Lenguaje humano, simple y natural
- Acompaña emocionalmente
- No promociones
- No cierres con “Amén”
"""

    return prompt.strip()
