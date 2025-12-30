# generator/v3/adapter/persistence_adapter.py

import os

from generator.content.fingerprinter import generar_fingerprint_contenido
from db.repositories.video_repo import (
    insert_video,
    fingerprint_existe_ultimos_dias,
)
from generator.audio.selector import crear_audio


def persistir_video_v3(
    *,
    video_id: str,
    channel_id: int,
    tipo: str,
    output_path: str,
    texto: str,
    imagen_usada: str | None,
    musica_usada: str | None,
    fingerprint: str,
    usar_tts: bool,
    modo_test: bool,
    metadata_extra: dict | None = None,
    licencia_path: str | None = None,
):
    # -------------------------------------------------
    # Persistencia
    # -------------------------------------------------
    if not os.path.exists(output_path):
        raise RuntimeError(f"No existe el archivo final: {output_path}")

    if modo_test:
        print(f"[TEST] Video generado (no persistido): {output_path}")
        return

    try:
        insert_video({
            "id": video_id,
            "channel_id": channel_id,
            "archivo": output_path,
            "tipo": tipo,
            "musica": musica_usada,
            "licencia": licencia_path,
            "imagen": imagen_usada,
            "texto_base": texto,
            "fingerprint": fingerprint,
            "metadata": {
                "has_voice": usar_tts,
                **(metadata_extra or {}),
            },
        })
    except Exception:
        # rollback filesystem
        os.remove(output_path)
        raise
