# tests/v2/content/test_parser.py

import pytest

from generator.v2.content.parser import (
    parse_content,
    ContentBlock,
    ParsedContent,
)


# -------------------------------------------------
# Plain mode
# -------------------------------------------------

def test_parse_plain_single_block():
    raw = """
    Señor, te doy gracias por este día.
    Dame fuerza y paz.
    """

    result = parse_content(
        raw_text=raw,
        title="Oración de prueba",
        mode="plain"
    )

    assert isinstance(result, ParsedContent)
    assert result.title == "Oración de prueba"
    assert len(result.blocks) == 1
    assert isinstance(result.blocks[0], ContentBlock)
    assert "Señor" in result.blocks[0].text
    assert "Dios" not in result.blocks[0].text  # no inventa texto


# -------------------------------------------------
# Stanzas mode
# -------------------------------------------------

def test_parse_stanzas_multiple_blocks():
    raw = """
    El Señor es mi pastor,
    nada me faltará.

    En verdes praderas me hace descansar.

    Guía mis pasos por senderos de justicia.
    """

    result = parse_content(
        raw_text=raw,
        title="Salmo 23",
        mode="stanzas"
    )

    assert result.title == "Salmo 23"
    assert len(result.blocks) == 3

    texts = [b.text for b in result.blocks]
    assert "pastor" in texts[0].lower()
    assert "praderas" in texts[1].lower()
    assert "senderos" in texts[2].lower()


# -------------------------------------------------
# Max blocks
# -------------------------------------------------

def test_parse_stanzas_with_max_blocks():
    raw = """
    Estrofa uno.

    Estrofa dos.

    Estrofa tres.

    Estrofa cuatro.
    """

    result = parse_content(
        raw_text=raw,
        title="Salmo corto",
        mode="stanzas",
        max_blocks=2
    )

    assert len(result.blocks) == 2
    assert result.blocks[0].text == "Estrofa uno."
    assert result.blocks[1].text == "Estrofa dos."


# -------------------------------------------------
# Normalization
# -------------------------------------------------

def test_normalization_replaces_common_words():
    raw = """
    Senor, tu eres mi dios.
    """

    result = parse_content(
        raw_text=raw,
        title="Normalización",
        mode="plain",
        normalize=True
    )
    
    text = result.blocks[0].text

    assert "Señor" in text
    assert "Dios" in text
    assert "Senor" not in text
    assert " dios " not in text.lower()


def test_disable_normalization():
    raw = "Senor mio"

    result = parse_content(
        raw_text=raw,
        title="Sin normalizar",
        mode="plain",
        normalize=False
    )

    assert result.blocks[0].text == "Senor mio"


# -------------------------------------------------
# Errors
# -------------------------------------------------

def test_empty_text_raises_error():
    with pytest.raises(ValueError):
        parse_content(
            raw_text="   ",
            title="Vacío",
            mode="plain"
        )


def test_invalid_mode_raises_error():
    with pytest.raises(ValueError):
        parse_content(
            raw_text="texto",
            title="Modo inválido",
            mode="unknown"  # type: ignore
        )
