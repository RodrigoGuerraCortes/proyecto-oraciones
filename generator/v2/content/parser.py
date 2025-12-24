# generator/v2/content/parser.py

from dataclasses import dataclass
from typing import List, Literal


ContentMode = Literal["plain", "stanzas"]


@dataclass(frozen=True)
class ContentBlock:
    """
    Representa un bloque lógico de contenido.
    Ej:
    - una oración completa
    - una estrofa de un salmo
    """
    text: str


@dataclass(frozen=True)
class ParsedContent:
    """
    Resultado del parseo de contenido.
    """
    title: str
    blocks: List[ContentBlock]


# -------------------------------------------------
# API pública
# -------------------------------------------------

def parse_content(
    *,
    raw_text: str,
    title: str,
    mode: ContentMode,
    max_blocks: int | None = None,
    normalize: bool = True
) -> ParsedContent:
    """
    Parsea texto crudo en bloques lógicos según el modo.

    - plain: todo el texto es un solo bloque
    - stanzas: divide por doble salto de línea

    Args:
        raw_text: texto completo del archivo
        title: título del contenido
        mode: "plain" | "stanzas"
        max_blocks: límite máximo de bloques (opcional)
        normalize: aplica normalizaciones básicas al texto

    Returns:
        ParsedContent
    """

    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text vacío")

    if mode == "plain":
        blocks = [_build_block(raw_text, normalize)]

    elif mode == "stanzas":
        blocks = _parse_stanzas(
            raw_text,
            normalize=normalize,
            max_blocks=max_blocks
        )

    else:
        raise ValueError(f"Modo de contenido no soportado: {mode}")

    return ParsedContent(
        title=title.strip(),
        blocks=blocks
    )


# -------------------------------------------------
# Implementaciones internas
# -------------------------------------------------

def _parse_stanzas(
    raw_text: str,
    *,
    normalize: bool,
    max_blocks: int | None
) -> List[ContentBlock]:

    partes = [
        p.strip()
        for p in raw_text.split("\n\n")
        if p.strip()
    ]

    if max_blocks is not None:
        partes = partes[:max_blocks]

    return [
        _build_block(p, normalize)
        for p in partes
    ]


def _build_block(text: str, normalize: bool) -> ContentBlock:
    if normalize:
        text = _normalize_text(text)

    return ContentBlock(text=text)


# -------------------------------------------------
# Normalización
# -------------------------------------------------

def _normalize_text(text: str) -> str:
    """
    Normalizaciones suaves, editoriales.
    NO debe hacer transformaciones agresivas.
    """

    reemplazos = {
        " senor ": " señor ",
        "Senor": "Señor",
        "dios": "Dios",
        " dios ": " Dios ",
        "\r": "",
    }

    for src, dst in reemplazos.items():
        text = text.replace(src, dst)

    # Limpieza básica de espacios
    text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    return text.strip()
