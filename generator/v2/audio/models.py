# generator/v2/audio/models.py

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TTSBlock:
    text: str
    start: float
    duration: float

@dataclass
class AudioRequest:
    duration: float
    music_duration: float | None = None
    music_enabled: bool = True
    music_base_path: str | None = None
    music_fixed: Optional[str] = None
    music_volume: float = 0.35

    tts_enabled: bool = False
    tts_text: Optional[str] = None
    tts_blocks: Optional[List[TTSBlock]] = None
    tts_ratio: float = 1.0
    
    # NUEVO: estrategia TTS
    tts_mode: str = "continuous"  # "continuous" | "blocks"
    pause_after_title: float = 0.0
    pause_between_blocks: float = 0.0

    voice_volume: float = 1.0


@dataclass
class AudioResult:
    def __init__(
        self,
        audio_clip,
        music_used=None,
        tts_duration: float = 0.0,
    ):
        self.audio_clip = audio_clip
        self.music_used = music_used
        self.tts_duration = tts_duration
