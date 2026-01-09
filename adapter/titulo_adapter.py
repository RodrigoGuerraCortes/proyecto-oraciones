# adapter/titulo_adapter.py

from generator.titulo import crear_imagen_titulo

def crear_imagen_titulo_v3(
    *,
    titulo: str,
    output: str,
    font: str | None = None,
    font_size: int | None = None,
    color: str | None = None,
    shadow: bool | None = None,
    max_width_chars: int | None = None,
    line_spacing: int | None = None,
):
    """
    Adapter v3 → v1.

    Por ahora:
    - v1 controla fuente, color y layout
    - v3 solo pasa título + output

    Más adelante, cuando retiremos v1,
    esta función absorberá la lógica.
    """

    # Ignoramos parámetros visuales por ahora (v1 legacy)
    return crear_imagen_titulo(titulo, output)
