# generator/content/tag.py
import hashlib


def generar_tag_inteligente(tipo: str, texto: str, imagen: str, musica: str, duracion: float) -> str:
    """
    Tag estable según:
    - tipo
    - hash de texto
    - imagen usada
    - música usada
    - duración final (incluyendo CTA si aplica)
    """
    texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]
    contenido = f"{tipo}|{texto_hash}|{imagen}|{musica}|{duracion}"
    h = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
    return h[:16]
