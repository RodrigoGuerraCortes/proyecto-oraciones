# generator/v2/pipeline/models.py

from dataclasses import dataclass


@dataclass
class PipelineRequest:
    channel_id: int
    format_code: str          # ej: "short_oracion"
    quantity: int
    modo_test: bool = False
