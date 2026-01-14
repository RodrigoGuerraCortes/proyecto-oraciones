# engine/timeline/blocks/tts_sequence.py


class TTSSequenceBlock:
    def __init__(self, block: dict, ctx):
        self.block = block
        self.ctx = ctx

    def run(self):
        """
        block = {
          "id": "guia_contemplativa",
          "type": "tts_sequence",
          "source": "script_guiados/FORMATO_A.txt",
          "output": "script_guiados/FORMATO_A",
          "pause_between": 2.5
        }
        """

        source = self.block["source"]
        output_dir = self.block.get("output", "default")
        pause_between = self.block.get("pause_between", 0.0)

        self.ctx.generar_tts_sequence(
            source=source,
            output_dir=output_dir,
            pause_between=pause_between,
        )
