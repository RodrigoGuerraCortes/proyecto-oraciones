# generator/v2/content/layout/segmentation.py

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
    Divide texto en bloques VISUALES.
    - Nunca excede max_lineas por bloque.
    - Regla Amén: nunca queda solo, se une a la línea anterior.
    - Regla balance: si el último bloque queda muy corto, se balancea.
    """

    # -------------------------------------------------
    # 1) Normalización previa (regla Amén)
    # -------------------------------------------------
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    if len(lineas) >= 2 and lineas[-1].lower().rstrip(".") in ("amen", "amén"):
        # "Amén" SIEMPRE se une a la línea anterior (misma pantalla)
        lineas[-2] = lineas[-2].rstrip(".") + ".\nAmén"
        lineas.pop()

    texto = "\n".join(lineas)

    # -------------------------------------------------
    # 2) Wrap por ancho real (PIL)
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

    # -------------------------------------------------
    # 3) Cortar en bloques de máximo max_lineas
    #    intentando cortes semánticos cerca del ideal
    # -------------------------------------------------
    bloques: list[str] = []
    i = 0

    while i < len(wrapped_lines):
        ideal = i + max_lineas

        # caso final
        if ideal >= len(wrapped_lines):
            restante = wrapped_lines[i:]
            while len(restante) > max_lineas:
                bloques.append("\n".join(restante[:max_lineas]))
                restante = restante[max_lineas:]
            if restante:
                bloques.append("\n".join(restante))
            break

        corte = _buscar_punto_corte(
            wrapped_lines,
            ideal=ideal,
            tolerancia=2,
        )

        # seguridad: nunca overflow
        if corte - i > max_lineas:
            corte = ideal

        bloques.append("\n".join(wrapped_lines[i:corte]))
        i = corte

    # -------------------------------------------------
    # 4) Regla editorial: balancear último bloque si queda muy corto
    # -------------------------------------------------
    MIN_LINEAS_ULTIMO = 5

    if len(bloques) >= 2:
        ultimo = bloques[-1]
        lineas_ultimo = [l for l in ultimo.splitlines() if l.strip()]

        if len(lineas_ultimo) < MIN_LINEAS_ULTIMO:
            anterior = bloques[-2]
            lineas_anterior = [l for l in anterior.splitlines() if l.strip()]

            # mover líneas desde el final del bloque anterior al inicio del último
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
    Devuelve el índice de corte (exclusivo).
    """

    if ideal >= len(lineas):
        return len(lineas)

    prioridades = [
        ".",   # cierre fuerte
        ":",   # pausa larga
        ";",   # pausa media
        ",",   # pausa débil
    ]

    inicio = max(0, ideal - tolerancia)
    fin = min(len(lineas) - 1, ideal + tolerancia)

    for signo in prioridades:
        for i in range(inicio, fin + 1):
            if lineas[i].strip().endswith(signo):
                return i + 1

    return ideal
