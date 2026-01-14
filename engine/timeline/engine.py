# engine/timeline/engine.py

from engine.timeline.blocks.tts import TTSBlock
from engine.timeline.blocks.tts_sequence import TTSSequenceBlock
from engine.timeline.blocks.silence import SilenceBlock


BLOCK_REGISTRY = {
    "tts": TTSBlock,
    "tts_sequence": TTSSequenceBlock,
    "silence": SilenceBlock,
}

class TimelineEngine:
    def __init__(self, ctx):
        self.ctx = ctx

    def run(self, narrative: dict):
        blocks = narrative.get("blocks", [])

        for block in blocks:
            self.run_block(block)

    def run_block(self, block: dict):
        block_type = block.get("type")

        if block_type not in BLOCK_REGISTRY:
            raise ValueError(f"Unsupported block type: {block_type}")

        block_class = BLOCK_REGISTRY[block_type]
        block_instance = block_class(block, self.ctx)
        block_instance.run()
