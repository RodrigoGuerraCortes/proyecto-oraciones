# generator/v2/content/segmentation.py

from PIL import Image, ImageDraw, ImageFont
from generator.v2.video.text_wrap import wrap_text_by_width


def dividir_en_bloques_por_lineas(
    *,
    texto: str,
    font_path: str,
    font_size: int,
    max_width_px: int,
    max_lineas: int = 8,
) -> list[str]:

    img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)

    wrapped_lines = wrap_text_by_width(
        text=texto,
        font=font,
        max_width_px=max_width_px,
        draw=draw,
    )

    bloques: list[str] = []

    i = 0
    while i < len(wrapped_lines):
        ideal = i + max_lineas

        if ideal >= len(wrapped_lines):
            bloques.append("\n".join(wrapped_lines[i:]))
            break

        corte = _buscar_punto_corte(
            wrapped_lines,
            ideal=ideal,
            tolerancia=2,
        )

        bloques.append("\n".join(wrapped_lines[i:corte]))
        i = corte

    # regla "Amén"
    if len(bloques) >= 2:
        ult = bloques[-1].strip().lower().rstrip(".")
        if ult in ("amen", "amén"):
            bloques[-2] += "\nAmén"
            bloques.pop()

    return bloques


def _buscar_punto_corte(
    lineas: list[str],
    ideal: int,
    tolerancia: int = 2,
) -> int:
    """
    Busca un punto de corte natural alrededor del índice ideal.
    Considera +/- tolerancia líneas.
    Devuelve el índice de corte (exclusivo).
    """

    if ideal >= len(lineas):
        return len(lineas)

    prioridades = [
        ".",   # cierre fuerte
        ":",   # introducción / pausa larga
        ";",   # pausa media
        ",",   # pausa débil (último recurso)
    ]

    inicio = max(0, ideal - tolerancia)
    fin = min(len(lineas) - 1, ideal + tolerancia)

    # 1) Buscar por prioridad de signos
    for signo in prioridades:
        for i in range(inicio, fin + 1):
            if lineas[i].strip().endswith(signo):
                return i + 1

    # 2) Fallback: corte mecánico
    return ideal




def calcular_duracion_bloque(texto: str) -> int:
    n = len([l for l in texto.splitlines() if l.strip()])
    if n <= 7:
        return 20
    elif n <= 12:
        return 28
    else:
        return 35
