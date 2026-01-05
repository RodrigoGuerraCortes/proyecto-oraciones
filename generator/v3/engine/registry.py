# generator/v3/engine/registry.py

from generator.v3.long.generar_long_guiado_generico import generar_long_guiado_generico
from generator.v3.short.generar_short_stanza_generico import generar_short_stanza_generico
from generator.v3.short.generar_short_plain_generico import generar_short_plain


ENGINE_REGISTRY = {
    "short_plain": generar_short_plain,
    "short_stanza": generar_short_stanza_generico,
    "long_guided": generar_long_guiado_generico,
}
