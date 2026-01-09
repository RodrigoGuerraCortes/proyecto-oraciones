from generator.texto import crear_imagen_texto 


def crear_imagen_texto_v3(
    *,
    texto: str,
    output: str,
    font: str | None = None,
    font_size: int | None = None,
    line_spacing: int | None = None,
    max_width: int | None = None,
    outline_px: int | None = None,
    outline_color: str | None = None,
):
    """
    Adapter v3 → v1.

    Por ahora:
    - v1 decide tipografía, tamaños y layout
    - v3 solo entrega texto + output

    Más adelante, cuando retiremos v1,
    esta función absorberá la lógica visual.
    """

    # Ignoramos parámetros visuales (legacy v1)
    return crear_imagen_texto(texto, output)
