# engine/timeline/context_long.py
import uuid
import os

from generator.audio.tts_edge import (
    generar_voz_edge,
    _normalizar_texto_tts,
    suavizar_finales_tts,
)
from generator.audio.silence import generar_silencio


class TimelineContextLong:
    def __init__(self, runtime):
        self.runtime = runtime

    # ----------------------------------
    # TTS simple
    # ----------------------------------
    def generar_tts(self, texto: str, output_dir: str):
        output_base = os.path.join(
            self.runtime.tts_output_dir,
            output_dir
        )
        os.makedirs(output_base, exist_ok=True)

        wav = os.path.join(
            output_base,
            f"tts_{uuid.uuid4().hex}.wav"
        )

        voz = generar_voz_edge(
            texto=suavizar_finales_tts(_normalizar_texto_tts(texto)),
            salida_wav=wav,
        ).set_start(self.runtime.t)

        self.runtime.voz_clips.append(voz)
        self.runtime.avanzar(float(voz.duration))

    # ----------------------------------
    # TTS sequence (guion guiado)
    # ----------------------------------
    def generar_tts_sequence(
        self,
        source: str,
        output_dir: str,
        pause_between: float,
    ):
        print(f"[TimelineContextLong] TTS sequence -> {source}")

        full_path = os.path.join(
            self.runtime.texts_base_path,
            source
        )

        if not os.path.exists(full_path):
            raise FileNotFoundError(full_path)

        with open(full_path, "r", encoding="utf-8") as f:
            lineas = [
                l.strip().strip('",')
                for l in f.readlines()
                if l.strip()
            ]

        for linea in lineas:
            self.generar_tts(
                texto=linea,
                output_dir=output_dir,
            )

            if pause_between > 0:
                generar_silencio(pause_between)
                self.runtime.avanzar(pause_between)

    # ----------------------------------
    # Silencio explícito
    # ----------------------------------
    def generar_silencio(self, seconds: float):
        generar_silencio(seconds)
        self.runtime.avanzar(seconds)
