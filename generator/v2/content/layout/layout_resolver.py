# generator/v2/content/layout/layout_resolver.py

from generator.v2.content.layout.plain_layout import layout_plain
from generator.v2.content.layout.stanzas_layout import layout_stanzas


def resolve_layout(
    *,
    parsed,
    content_cfg: dict,
    text_style,
):
    """
    Convierte ParsedContent (bloques lógicos) en bloques visuales
    listos para renderizar: [{text, duration}, ...]
    """

    mode = content_cfg["type"]  # "plain" | "stanzas"

    if mode == "plain":
        return layout_plain(
            parsed=parsed,
            content_cfg=content_cfg,
            text_style=text_style,
            tts_enabled=content_cfg.get("_tts_enabled", False),
        )

    if mode == "stanzas":
        return layout_stanzas(
            parsed=parsed,
            content_cfg=content_cfg,
        )

    raise ValueError(f"Unsupported content type: {mode}")
