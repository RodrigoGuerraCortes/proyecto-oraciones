# generator/fingerprinter.py
import hashlib


def generar_fingerprint_contenido(
    tipo: str,
    texto: str,
    imagen: str,
    musica: str,
    duracion: float
) -> str:
    texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]
    contenido = f"{tipo}|{texto_hash}|{imagen}|{musica}|{duracion}"
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()[:16]
