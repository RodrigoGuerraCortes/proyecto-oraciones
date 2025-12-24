# generator/v2/cleanup/models.py

from dataclasses import dataclass
from typing import List


@dataclass
class TempFilesContext:
    """
    Contexto explícito de archivos temporales creados
    durante un render.
    """
    files: List[str]
    directories: List[str] | None = None
