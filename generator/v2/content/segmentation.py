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
    """
    Divide el texto en bloques visuales.
    Regla de oro: ningún bloque puede exceder max_lineas visibles.
    """

    # -------------------------------------------------
    # 1) Normalización previa (ÚNICO lugar donde se trata "Amén")
    # -------------------------------------------------
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    if len(lineas) >= 2 and lineas[-1].lower().rstrip(".") in ("amen", "amén"):
        # "Amén" SIEMPRE se une a la línea anterior
        lineas[-2] = lineas[-2].rstrip(".") + ".\nAmén"
        lineas.pop()

    texto = "\n".join(lineas)

    # -------------------------------------------------
    # 2) Preparar medición real de texto
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 3) Segmentación visual + semántica
    # -------------------------------------------------
    i = 0
    while i < len(wrapped_lines):
        ideal = i + max_lineas

        # Caso final: lo que queda
        if ideal >= len(wrapped_lines):
            restante = wrapped_lines[i:]

            # Forzar chunks de max_lineas (nunca overflow visual)
            while len(restante) > max_lineas:
                bloques.append("\n".join(restante[:max_lineas]))
                restante = restante[max_lineas:]

            if restante:
                bloques.append("\n".join(restante))

            break

        # Intentar corte semántico cercano
        corte = _buscar_punto_corte(
            wrapped_lines,
            ideal=ideal,
            tolerancia=2,
        )

        # Seguridad: nunca permitir overflow visual
        if corte - i > max_lineas:
            corte = ideal

        bloques.append("\n".join(wrapped_lines[i:corte]))
        i = corte

        # -------------------------------------------------
        # Regla editorial: balancear último bloque si es muy corto
        # -------------------------------------------------
        MIN_LINEAS_ULTIMO = 5

    if len(bloques) >= 2:
        ultimo = bloques[-1]
        lineas_ultimo = [l for l in ultimo.splitlines() if l.strip()]

        if len(lineas_ultimo) < MIN_LINEAS_ULTIMO:
            anterior = bloques[-2]
            lineas_anterior = [l for l in anterior.splitlines() if l.strip()]

            # mover líneas desde el final del bloque anterior
            while (
                len(lineas_ultimo) < MIN_LINEAS_ULTIMO
                and len(lineas_anterior) > MIN_LINEAS_ULTIMO
            ):
                linea_movida = lineas_anterior.pop()
                lineas_ultimo.insert(0, linea_movida)

            bloques[-2] = "\n".join(lineas_anterior)
            bloques[-1] = "\n".join(lineas_ultimo)


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
    """
    Duración sugerida por cantidad de líneas visibles.
    """
    n = len([l for l in texto.splitlines() if l.strip()])

    if n <= 7:
        return 20
    elif n <= 12:
        return 28
    else:
        return 35
