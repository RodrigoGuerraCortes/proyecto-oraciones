from __future__ import annotations

# generator/v3/publisher/base.py
print(">>> BASE PUBLISHER NUEVO CARGADO <<<")


import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from db.connection import get_connection


class BasePublisher:
    """
    Worker base para publicación de videos.

    Responsabilidades:
    - Elegir publicaciones desde DB
    - (modo normal) Lockear y publicar UNA
    - (dry-run) Mostrar qué se publicaría
    """

    platform_code: Optional[str] = None
    allow_future_publication: bool = True
    max_days_a_publicar: int = 30  # requerido si allow_future_publication=True

    # Default dry-run horizon (tu lo cambiaste a 15 días)
    dry_run_default_days: int = 15

    # -----------------------------
    # Public entrypoint
    # -----------------------------
    def run(self, *, dry_run: bool = False, preview_days: Optional[int] = None, force_now: bool = False):
        if not self.platform_code:
            raise RuntimeError("platform_code no definido")

        now = datetime.now()
        limite = self._calcular_limite(now=now, dry_run=dry_run, preview_days=preview_days, force_now=force_now)

        with get_connection() as conn:
            with conn.cursor() as cur:
                platform_id = self._get_platform_id(cur)

                publicaciones = self._fetch_publicaciones(
                    cur=cur,
                    platform_id=platform_id,
                    limite=limite,
                    force_now=force_now,
                )

                print(f"[{self.platform_code.upper()}] Buscando publicaciones hasta {limite}...")

                if not publicaciones:
                    print(f"[{self.platform_code.upper()}] No hay publicaciones en el rango.")
                    return

                # DRY RUN → solo mostrar
                if dry_run:
                    self._dry_run(now=now, limite=limite, publicaciones=publicaciones)
                    return

                # MODO REAL → UNA publicación
                row = publicaciones[0]
                payload = self._build_publication_payload(row=row)

                # Lock lógico (en TX)
                self._lock_publication(cur=cur, now=now, publication_id=payload["publication_id"])
                conn.commit()

        # Publicar fuera de TX
        self._publish_outside_tx(payload)

    # -----------------------------
    # Core helpers
    # -----------------------------
    def _calcular_limite(
        self,
        *,
        now: datetime,
        dry_run: bool,
        preview_days: Optional[int],
        force_now: bool,
    ) -> datetime:
        # Override explícito (testing / emergencia)
        if force_now:
            return now

        # Dry-run SIEMPRE puede mirar al futuro (editorial)
        if dry_run:
            if preview_days is not None:
                return now + timedelta(days=int(preview_days))
            return now + timedelta(days=self.dry_run_default_days)

        # Modo real
        if self.allow_future_publication:
            if not self.max_days_a_publicar:
                raise RuntimeError("max_days_a_publicar requerido para publicaciones futuras")
            return now + timedelta(days=self.max_days_a_publicar)

        return now

    def _get_platform_id(self, cur) -> int:
        cur.execute("SELECT id FROM platforms WHERE code = %s", (self.platform_code,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"Platform '{self.platform_code}' no existe")
        return row["id"] if isinstance(row, dict) else row[0]

    def _fetch_publicaciones(self, *, cur, platform_id: int, limite: datetime, force_now: bool):
        base_select = """
            SELECT
                p.id           AS publication_id,
                p.publicar_en  AS publicar_en,
                v.archivo      AS archivo,
                v.tipo         AS tipo,
                v.licencia     AS licencia,
                v.texto_base   AS texto_base,
                c.config       AS channel_config
            FROM publications p
            JOIN videos v ON v.id = p.video_id
            JOIN channel_configs c ON c.channel_id = v.channel_id
            WHERE p.platform_id = %s
              AND p.estado = 'scheduled'
        """

        if force_now:
            sql = base_select + " ORDER BY p.publicar_en ASC"
            cur.execute(sql, (platform_id,))
        else:
            sql = base_select + " AND p.publicar_en <= %s ORDER BY p.publicar_en ASC"
            cur.execute(sql, (platform_id, limite))

        return cur.fetchall()

    def _dry_run(self, *, now: datetime, limite: datetime, publicaciones):
        print(f"\n===== DRY RUN {self.platform_code.upper()} =====")
        print(f"Fecha actual : {now}")
        print(f"Hasta        : {limite}")

        for row in publicaciones:
            # Importante: preview debe recibir editorial_cfg ya resuelta para que sea “what you will publish”
            payload = self._build_publication_payload(row=row)
            self.preview_publication(**payload)

        print(f"===== FIN DRY RUN {self.platform_code.upper()} =====\n")

    def _lock_publication(self, *, cur, now: datetime, publication_id: int):
        cur.execute(
            """
            UPDATE publications
            SET estado = 'publishing',
                fecha_intento = %s
            WHERE id = %s
            """,
            (now, publication_id),
        )

    def _publish_outside_tx(self, payload: Dict[str, Any]):
        try:
            external_id = self.publish_video(**payload)

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
                        (datetime.now(), external_id, payload["publication_id"]),
                    )
                conn2.commit()

            print(
                f"[{self.platform_code.upper()}] "
                f"Publicado: {payload['archivo']} "
                f"(publish_at={payload['publicar_en']})"
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
                        (str(e), payload["publication_id"]),
                    )
                conn2.commit()

            print(f"[{self.platform_code.upper()} ERROR] {payload['archivo']} → {e}")
            # Re-raise opcional (útil en CI / monitoreo)
            raise

    # -----------------------------
    # Payload builder (centraliza)
    # -----------------------------
    def _build_publication_payload(self, *, row: Dict[str, Any]) -> Dict[str, Any]:
        publication_id = row["publication_id"]
        archivo = row["archivo"]
        publicar_en = row["publicar_en"]
        tipo = row["tipo"]
        licencia = row["licencia"]
        texto_base = row["texto_base"]

        channel_config = self._ensure_dict(row.get("channel_config"))
        editorial_cfg = self._get_editorial_cfg(channel_config=channel_config, tipo=tipo)

        return {
            "archivo": archivo,
            "publicar_en": publicar_en,
            "publication_id": publication_id,
            "tipo": tipo,
            "licencia": licencia,
            "texto_base": texto_base,
            "editorial_cfg": editorial_cfg,
            # Si luego quieres pasar config completo, ya está disponible:
            "channel_config": channel_config,
        }

    # -----------------------------
    # Métodos a implementar por plataforma
    # -----------------------------
    def publish_video(
        self,
        *,
        archivo: str,
        publicar_en: datetime,
        publication_id: int,
        tipo: str,
        licencia: str,
        texto_base: str,
        editorial_cfg: Dict[str, Any],
        channel_config: Dict[str, Any],
    ):
        raise NotImplementedError

    def preview_publication(
        self,
        *,
        archivo: str,
        publicar_en: datetime,
        publication_id: int,
        tipo: str,
        licencia: str,
        texto_base: str,
        editorial_cfg: Dict[str, Any],
        channel_config: Dict[str, Any],
    ):
        raise NotImplementedError

    # -----------------------------
    # Métodos auxiliares comunes
    # -----------------------------
    def _get_editorial_cfg(self, *, channel_config: Dict[str, Any], tipo: str) -> Dict[str, Any]:
        editorial = channel_config.get("editorial")

        print(f"Editorial config: {editorial}")

        if not editorial:
            raise RuntimeError("Channel sin configuración editorial")

        tipos = editorial.get("tipos", {})
        if tipo not in tipos:
            raise RuntimeError(f"Tipo '{tipo}' no definido en editorial del canal")

        return {
            "code": editorial.get("code"),
            "language": editorial.get("language"),
            "contextos": editorial.get("contextos", []),
            "tipo_cfg": tipos[tipo],
        }

    def _ensure_dict(self, value) -> Dict[str, Any]:
        """
        PostgreSQL JSONB puede venir como dict (psycopg2/real dict cursor)
        o como str. Esta función normaliza a dict.
        """
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception as e:
                raise RuntimeError(f"channel_config no es JSON válido: {e}")
        # fallback: intentar convertir (ej: psycopg JSON)
        try:
            return dict(value)  # type: ignore[arg-type]
        except Exception:
            raise RuntimeError(f"channel_config type no soportado: {type(value)}")
