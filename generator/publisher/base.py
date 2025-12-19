# generator/publisher/base.py
print(">>> BASE PUBLISHER NUEVO CARGADO <<<")

from datetime import datetime, timedelta
from db.connection import get_connection


class BasePublisher:
    """
    Worker base para publicación de videos.

    Responsabilidades:
    - Elegir publicaciones desde DB
    - (modo normal) Lockear y publicar UNA
    - (dry-run) Mostrar qué se publicaría
    """

    platform_code = None
    allow_future_publication = False
    max_days_a_publicar = None  # requerido si allow_future_publication=True

    def run(self, *, dry_run=False, preview_days=None, force_now=False):
        if not self.platform_code:
            raise RuntimeError("platform_code no definido")

        now = datetime.now()

        # -------------------------------------------------
        # 1️⃣ Calcular límite temporal (REFACTORIZADO)
        # -------------------------------------------------
        if force_now:
            # Override explícito (testing / emergencia)
            limite = now

        elif dry_run:
            # Dry-run SIEMPRE puede mirar al futuro (editorial)
            if preview_days:
                limite = now + timedelta(days=preview_days)
            else:
                # Default: 24 horas
                limite = now + timedelta(days=1)

        else:
            # Modo real
            if self.allow_future_publication:
                if not self.max_days_a_publicar:
                    raise RuntimeError(
                        "max_days_a_publicar requerido para publicaciones futuras"
                    )
                limite = now + timedelta(days=self.max_days_a_publicar)
            else:
                limite = now

        with get_connection() as conn:
            with conn.cursor() as cur:

                # -------------------------------------------------
                # 2️⃣ platform_id
                # -------------------------------------------------
                cur.execute(
                    "SELECT id FROM platforms WHERE code = %s",
                    (self.platform_code,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(
                        f"Platform '{self.platform_code}' no existe"
                    )

                platform_id = row["id"] if isinstance(row, dict) else row[0]

                # -------------------------------------------------
                # 3️⃣ Buscar publicaciones
                # -------------------------------------------------
                if force_now:
                    cur.execute(
                        """
                        SELECT
                            p.id           AS publication_id,
                            p.publicar_en  AS publicar_en,
                            v.archivo      AS archivo,
                            v.tipo         AS tipo,
                            v.licencia     AS licencia,
                            v.texto_base   AS texto_base
                        FROM publications p
                        JOIN videos v ON v.id = p.video_id
                        WHERE p.platform_id = %s
                        AND p.estado = 'scheduled'
                        ORDER BY p.publicar_en ASC
                        """,
                        (platform_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            p.id           AS publication_id,
                            p.publicar_en  AS publicar_en,
                            v.archivo      AS archivo,
                            v.tipo         AS tipo,
                            v.licencia     AS licencia,
                            v.texto_base   AS texto_base
                        FROM publications p
                        JOIN videos v ON v.id = p.video_id
                        WHERE p.platform_id = %s
                        AND p.estado = 'scheduled'
                        AND p.publicar_en <= %s
                        ORDER BY p.publicar_en ASC
                        """,
                        (platform_id, limite),
                    )


                publicaciones = cur.fetchall()

                if not publicaciones:
                    print(
                        f"[{self.platform_code.upper()}] "
                        "No hay publicaciones en el rango."
                    )
                    return

                # -------------------------------------------------
                # 4️⃣ DRY RUN → solo mostrar
                # -------------------------------------------------
                if dry_run:
                    print(
                        f"\n===== DRY RUN {self.platform_code.upper()} ====="
                    )
                    print(f"Fecha actual : {now}")
                    print(f"Hasta        : {limite}")

                    for row in publicaciones:
                        self.preview_publication(**row)

                    print(
                        f"===== FIN DRY RUN {self.platform_code.upper()} =====\n"
                    )
                    return

                # -------------------------------------------------
                # 5️⃣ MODO REAL → UNA publicación
                # -------------------------------------------------
                row = publicaciones[0]

                publication_id = row["publication_id"]
                archivo = row["archivo"]
                publicar_en = row["publicar_en"]
                tipo = row["tipo"]
                licencia = row["licencia"]
                texto_base = row["texto_base"]

                # Lock lógico
                cur.execute(
                    """
                    UPDATE publications
                    SET estado = 'publishing',
                        fecha_intento = %s
                    WHERE id = %s
                    """,
                    (now, publication_id),
                )
                conn.commit()

        # -------------------------------------------------
        # 6️⃣ Publicar fuera de TX
        # -------------------------------------------------
        try:
            external_id = self.publish_video(
                archivo=archivo,
                publicar_en=publicar_en,
                publication_id=publication_id,
                tipo=tipo,
                licencia=licencia,
                texto_base=texto_base,
            )

            with get_connection() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(
                        """
                        UPDATE publications
                        SET estado = 'published',
                            fecha_publicado = %s,
                            external_id = %s
                        WHERE id = %s
                        """,
                        (datetime.now(), external_id, publication_id),
                    )
                conn2.commit()

            print(
                f"[{self.platform_code.upper()}] "
                f"Publicado: {archivo} "
                f"(publish_at={publicar_en})"
            )

        except Exception as e:
            with get_connection() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(
                        """
                        UPDATE publications
                        SET estado = 'failed',
                            error = %s
                        WHERE id = %s
                        """,
                        (str(e), publication_id),
                    )
                conn2.commit()

            print(
                f"[{self.platform_code.upper()} ERROR] "
                f"{archivo} → {e}"
            )

    # -------------------------------------------------
    # Métodos a implementar por plataforma
    # -------------------------------------------------
    def publish_video(
        self,
        *,
        archivo,
        publicar_en,
        publication_id,
        tipo,
        licencia,
        texto_base,
    ):
        raise NotImplementedError

    def preview_publication(self, **kwargs):
        raise NotImplementedError
