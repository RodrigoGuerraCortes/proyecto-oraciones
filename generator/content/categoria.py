# generator/content/categoria.py
# generator/content/categoria.py
import random

def decidir_categoria_video(tipo: str, titulo: str, texto: str) -> str:
    t = f"{titulo} {texto}".lower()

    # Prioridad explícita
    if any(k in t for k in ["espíritu santo", "espiritu santo"]):
        return "espiritu_santo"

    if any(k in t for k in ["jesús", "cristo", "señor jesús"]):
        if any(k in t for k in ["maría", "virgen", "madre"]):
            return "jesus_maria"
        return "jesus"

    if any(k in t for k in ["maría", "virgen", "madre de dios"]):
        return "maria"

    if any(k in t for k in ["josé", "san josé", "jose"]):
        if any(k in t for k in ["niño", "jesús"]):
            return "jose_jesus_niño"

    if any(k in t for k in ["papa", "pontífice", "vaticano"]):
        return "papa"

    if any(k in t for k in ["misa", "eucaristía", "comunión"]):
        return "misa"

    if any(k in t for k in ["cruz", "crucifixión", "calvario"]):
        return "cruz"

    if any(k in t for k in ["ángel", "arcángel", "miguel", "gabriel", "rafael"]):
        return "angel"

    if any(k in t for k in ["creación", "naturaleza", "montaña", "cielo", "mar"]):
        return "naturaleza"

    # Fallback neutro distribuido
    fallback = random.choices(
        population=["naturaleza", "angel", "misa", "cielo"],
        weights=[0.35, 0.25, 0.20, 0.15],
        k=1
    )[0]

    return fallback
