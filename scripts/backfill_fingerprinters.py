#!/usr/bin/env python3

import hashlib
from db.connection import get_connection


def generar_fingerprint(
    tipo: str,
    texto: str,
    imagen: str | None,
    musica: str | None,
    duracion: float | None,
) -> str:
    """
    Fingerprint estable del contenido.
    """
    texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]

    contenido = (
        f"{tipo}|"
        f"{texto_hash}|"
        f"{imagen or ''}|"
        f"{musica or ''}|"
        f"{duracion or 0}"
    )
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()[:32]


def main():
    print("🔍 Buscando videos sin fingerprint...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    tipo,
                    texto_base,
                    imagen,
                    musica
                FROM videos
                WHERE fingerprint IS NULL
            """)

            videos = cur.fetchall()

    if not videos:
        print("✅ No hay videos pendientes")
        return

    print(f"📦 Encontrados {len(videos)} videos")

    with get_connection() as conn:
        with conn.cursor() as cur:
            for v in videos:
                video_id = v["id"]

                fingerprint = generar_fingerprint(
                    tipo=v["tipo"],
                    texto=v["texto_base"],
                    imagen=v["imagen"],
                    musica=v["musica"],
                    duracion=None,  # no está en la tabla, ok dejarlo neutro
                )

                cur.execute("""
                    UPDATE videos
                    SET fingerprint = %(fp)s
                    WHERE id = %(id)s
                """, {
                    "fp": fingerprint,
                    "id": video_id
                })

                print(f"✔ fingerprint actualizado → {video_id}")

        conn.commit()

    print("🎉 Backfill completado correctamente")


if __name__ == "__main__":
    main()
