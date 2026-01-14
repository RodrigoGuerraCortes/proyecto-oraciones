# engine/timeline/blocks/silence.py

class SilenceBlock:
    def __init__(self, block: dict, ctx):
        self.block = block
        self.ctx = ctx

    def run(self):
        seconds = float(self.block.get("seconds", 0))
        if seconds > 0:
            self.ctx.generar_silencio(seconds)
