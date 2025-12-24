# generator/v2/audio/models.py

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class AudioRequest:
    duration: float
    
    music_enabled: bool = True
    music_fixed: Optional[str] = None
    music_volume: float = 0.35

    tts_enabled: bool = False
    tts_text: Optional[str] = None
    
    voice_volume: float = 1.0


@dataclass
class AudioResult:
    audio_clip: any
    music_used: Optional[str]
