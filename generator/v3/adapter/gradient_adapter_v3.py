# generator/v3/adapter/gradient_adapter_v3.py

# generator/v3/adapter/gradient_adapter_v3.py

import numpy as np
from moviepy.editor import VideoClip, ColorClip


def crear_gradiente_v3(
    *,
    duracion: float,
    size: tuple[int, int] = (1080, 1920),
    top_opacity: float = 0.0,
    bottom_opacity: float = 0.85,
    color: tuple[int, int, int] = (0, 0, 0),
):
    """
    Gradiente vertical estático compatible con MoviePy.

    - Máscara real (ismask=True)
    - Seguro para videos largos (60+ min)
    - Sin animaciones
    """

    width, height = size

    # -------------------------------------------------
    # Clip base de color
    # -------------------------------------------------
    base = ColorClip(
        size=size,
        color=color
    ).set_duration(duracion)

    # -------------------------------------------------
    # Construir máscara como VideoClip REAL
    # -------------------------------------------------
    gradient = np.linspace(
        top_opacity,
        bottom_opacity,
        height
    ).reshape((height, 1))

    gradient = np.repeat(gradient, width, axis=1)

    def make_mask_frame(t):
        return gradient

    mask = VideoClip(
        make_frame=make_mask_frame,
        ismask=True
    ).set_duration(duracion)

    # -------------------------------------------------
    # Aplicar máscara
    # -------------------------------------------------
    return base.set_mask(mask)
