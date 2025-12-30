# generator/v2/content/layout/stanzas_layout.py

from generator.v2.content.parser import ParsedContent


def layout_stanzas(
    *,
    parsed: ParsedContent,
    content_cfg: dict,
):
    """
    stanzas:
      - cada estrofa (bloque lógico) se convierte directamente en un bloque visual
      - duración fija por bloque (seconds_per_block)
    """
    seconds = float(content_cfg.get("seconds_per_block", 16))

    return [
        {"text": b.text, "duration": seconds}
        for b in parsed.blocks
    ]
