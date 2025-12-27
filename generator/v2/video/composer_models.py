# generator/v2/video/composer_models.py

from dataclasses import dataclass
from typing import List, Optional, Tuple
from moviepy.editor import ImageClip, AudioClip


@dataclass
class Overlay:
    clip: ImageClip
    start: float
    duration: float
    position: Tuple = ("center", "center")
    opacity: float = 1.0


@dataclass
class ComposerRequest:
    base_layers: List[ImageClip]        # fondo, gradiente
    overlays: List[Overlay]             # título, texto, watermark
    audio: AudioClip
    cta_layers: Optional[List[ImageClip]]
    output_path: str
    fps: int = 20


@dataclass
class ComposerResult:
    output_path: str
    duration: float
