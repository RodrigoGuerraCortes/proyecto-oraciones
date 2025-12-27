from PIL import ImageDraw, ImageFont


def wrap_text_by_width(
    *,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width_px: int,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    """
    Divide un texto en líneas según ancho real en píxeles.
    MISMO criterio que usa el renderer.
    """

    wrapped: list[str] = []

    for line in text.splitlines():
        words = line.split()
        current = ""

        for word in words:
            test = current + (" " if current else "") + word
            w = draw.textlength(test, font=font)

            if w <= max_width_px:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = word

        if current:
            wrapped.append(current)

    return wrapped
