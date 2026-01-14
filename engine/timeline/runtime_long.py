# engine/timeline/runtime_long.py

class LongRuntime:
    def __init__(self, *, texts_base_path: str, tts_output_dir: str):
        self.t = 0.0
        self.voz_clips = []

        self.texts_base_path = texts_base_path
        self.tts_output_dir = tts_output_dir

    def avanzar(self, seconds: float):
        self.t += seconds
        print(f"[LongRuntime] Avanzando {seconds} segundos. Tiempo actual: {self.t}")