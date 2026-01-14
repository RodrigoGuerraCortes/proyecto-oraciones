import json
from pathlib import Path

from engine.timeline.engine import TimelineEngine
from engine.timeline.context_long  import TimelineContextLong
from engine.timeline.runtime_long import LongRuntime

# Cargar narrativa
BASE_DIR = Path(__file__).resolve().parent.parent.parent
NARRATIVE_PATH = BASE_DIR / "narratives" / "long" / "oracion_guiada_v1.json"

with open(NARRATIVE_PATH, "r", encoding="utf-8") as f:
    narrative = json.load(f)

# Crear contexto de prueba
runtime = LongRuntime(
    texts_base_path="/mnt/storage/assets/texts/canal_catolico_01",
    tts_output_dir="/mnt/storage/generated/canal_catolico_01/longs",
)
ctx = TimelineContextLong(runtime=runtime)

# Ejecutar engine
engine = TimelineEngine(ctx)
engine.run(narrative)
