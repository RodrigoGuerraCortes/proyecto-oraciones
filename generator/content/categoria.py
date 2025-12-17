# generator/content/categoria.py
import os

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
        if "niño" in t or "jesús" in t:
            return "jose_jesus_nino"

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

    # Fallback seguro
    return "jesus"
