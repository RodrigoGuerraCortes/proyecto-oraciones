import re
import unicodedata
import yaml
from pathlib import Path


# -------------------------------------------------
# Carga de reglas desde YAML
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RULES_PATH = BASE_DIRRULES_PATH = BASE_DIR / "rules" / "es.yaml"

with open(RULES_PATH, "r", encoding="utf-8") as f:
    RULES_ES = yaml.safe_load(f)


# -------------------------------------------------
# Utilidades internas
# -------------------------------------------------
def _ascii_fold(text: str) -> str:
    """
    Convierte texto unicode a ASCII base (quita tildes)
    Ej: 'Oración' -> 'Oracion'
    """
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def _apply_title_case(words, lowercase_exceptions):
    """
    Aplica Title Case respetando excepciones
    """
    result = []
    for i, w in enumerate(words):
        lw = w.lower()
        if i > 0 and lw in lowercase_exceptions:
            result.append(lw)
        else:
            result.append(w.capitalize())
    return result


# -------------------------------------------------
# Normalizador principal Español
# -------------------------------------------------
def normalize_spanish(text: str) -> str:
    rules = RULES_ES

    options = rules.get("options", {})
    replacements = rules.get("replacements", [])
    patterns = rules.get("safe_patterns", [])
    protected = set(rules.get("protected_words", []))
    lowercase_exceptions = set(rules.get("lowercase_exceptions", []))

    # 1) Normalización unicode / ascii
    original_text = text
    working = text

    if options.get("normalize_unicode", True):
        working = unicodedata.normalize("NFC", working)

    folded = _ascii_fold(working) if options.get("ascii_fold_input", True) else working

    words_original = working.split()
    words_folded = folded.split()

    normalized_words = []

    for orig, fold in zip(words_original, words_folded):
        lw = fold.lower()

        # 2) Palabras protegidas (no tocar)
        if lw in protected:
            normalized_words.append(orig)
            continue

        replaced = False

        # 3) Reemplazos exactos
        for r in replacements:
            if lw == r["from"]:
                normalized_words.append(r["to"])
                replaced = True
                break

        if replaced:
            continue

        # 4) Reglas seguras por patrón
        for rule in patterns:
            if re.match(rule["pattern"], lw):
                normalized_words.append(
                    re.sub(rule["pattern"], rule["replace"], lw)
                )
                replaced = True
                break

        if replaced:
            continue

        # 5) Sin match → dejar palabra original
        normalized_words.append(orig)

    # 6) Title Case controlado
    if options.get("apply_title_case", True):
        normalized_words = _apply_title_case(
            normalized_words, lowercase_exceptions
        )

    return " ".join(normalized_words)
