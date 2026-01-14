# engine/timeline/blocks/tts.py

class TTSBlock:
    def __init__(self, block: dict, ctx):
        self.block = block
        self.ctx = ctx

    def run(self):
        """
        block = {
          "id": "titulo",
          "type": "tts",
          "source": "Oración Padre Nuestro",
          "output": "script_guiados/FORMATO_A",
          "pause_after": 1.5
        }
        """

        texto = self.block["source"]
        output_dir = self.block.get("output", "default")

        # Generar TTS
        self.ctx.generar_tts(
            texto=texto,
            output_dir=output_dir
        )

        # Pausa posterior (si existe)
        pause_after = self.block.get("pause_after")
        if pause_after:
            self.ctx.generar_silencio(pause_after)
