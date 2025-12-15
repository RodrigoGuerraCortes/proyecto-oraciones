from datetime import datetime, timedelta
from db.connection import get_connection


class BasePublisher:
    """
    Clase base para publishers de plataformas.

    - Publica videos en estado 'scheduled'
    - Limita cuántos días hacia adelante se publican (opcional)
    - NO decide horarios: publicar_en se usa solo para programar en la plataforma
    """

    platform_code = None
    max_days_a_publicar = None  # None = sin límite

    def run(self):
        if not self.platform_code:
            raise NotImplementedError("platform_code no definido")

        ahora = datetime.now()
        limite = (
            ahora + timedelta(days=self.max_days_a_publicar)
            if self.max_days_a_publicar
            else None
        )

        with get_connection() as conn:
            with conn.cursor() as cur:

                # -------------------------------------------------
                # 1. Obtener platform_id
                # -------------------------------------------------
                cur.execute(
                    "SELECT id FROM platforms WHERE code = %s",
                    (self.platform_code,)
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(
                        f"Platform '{self.platform_code}' no existe"
                    )

                platform_id = row["id"] if isinstance(row, dict) else row[0]

                # -------------------------------------------------
                # 2. Obtener publicaciones scheduled (con límite opcional)
                # -------------------------------------------------
                query = """
                    SELECT
                        p.id           AS id,
                        p.publicar_en  AS publicar_en,
                        v.archivo      AS archivo
                    FROM publications p
                    JOIN videos v ON v.id = p.video_id
                    WHERE p.platform_id = %s
                    AND p.estado IN ('scheduled', 'failed')
                    AND p.external_id IS NULL
                """
                params = [platform_id]

                if limite:
                    query += " AND p.publicar_en <= %s"
                    params.append(limite)

                query += " ORDER BY p.publicar_en"

                cur.execute(query, tuple(params))
                publicaciones = cur.fetchall()

                if not publicaciones:
                    print(
                        f"[{self.platform_code.upper()}] "
                        "No hay publicaciones dentro del rango."
                    )
                    return

                # -------------------------------------------------
                # 3. Publicar una por una
                # -------------------------------------------------
                for row in publicaciones:
                    pub_id = row["id"]
                    publicar_en = row["publicar_en"]
                    archivo = row["archivo"]

                    try:
                        video_id_externo = self.publish_video(
                            archivo=archivo,
                            publicar_en=publicar_en,
                            publication_id=pub_id
                        )
                        now = datetime.now()

                        cur.execute("""
                            UPDATE publications
                            SET estado = 'published',
                                fecha_intento = %s,
                                fecha_publicado = %s,
                                external_id = %s
                            WHERE id = %s
                        """, (now, now, video_id_externo, pub_id))

                        print(
                            f"[{self.platform_code.upper()}] "
                            f"Publicado → {archivo} "
                            f"(programado: {publicar_en})"
                        )

                    except Exception as e:
                        cur.execute("""
                            UPDATE publications
                            SET estado = 'failed',
                                fecha_intento = %s
                            WHERE id = %s
                        """, (datetime.now(), pub_id))

                        print(
                            f"[{self.platform_code.upper()} ERROR] "
                            f"{archivo} → {e}"
                        )

            conn.commit()

    def publish_video(self, archivo, publicar_en, publication_id):
        """
        Debe subir el video y retornar el ID externo
        (youtube_id, facebook_id, etc.)
        """
        raise NotImplementedError
