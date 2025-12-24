# generator/v2/video/background_selector/with_history.py

import os
import random
from db.connection import get_connection
from .base import BackgroundSelector
from generator.v2.video.background_selector.rule_engine import BackgroundRuleEngine
from db.repositories.background_rule_repo import get_background_rules

EXT_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")


class HistoryBackgroundSelector(BackgroundSelector):

    def __init__(
        self,
        *,
        base_path: str,
        ventana: int = 10,
        fallback: str = "default",
    ):
        self.base_path = base_path
        self.ventana = ventana
        self.fallback = fallback

    def elegir(
        self,
        *,
        text: str,
        title: str,
        format_code: str,
        channel_id: int,
    ) -> str:

        rules, fallback = get_background_rules(
            channel_id=channel_id,
            format_code=format_code,
        )

        engine = BackgroundRuleEngine(
            rules=rules,
            fallback=fallback,
        )

        categoria = engine.resolve(f"{title} {text}")

        carpeta = os.path.join(self.base_path, categoria)
        if not os.path.isdir(carpeta):
            categoria = self.fallback
            carpeta = os.path.join(self.base_path, categoria)

        archivos = [
            f for f in os.listdir(carpeta)
            if f.lower().endswith(EXT_VALIDAS)
        ]

        if not archivos:
            raise RuntimeError(f"No hay imágenes en {carpeta}")

        # -------- ventana anti-repetición (V1)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT imagen
                    FROM videos
                    WHERE imagen LIKE %s
                    ORDER BY fecha_generado DESC
                    LIMIT %s
                    """,
                    (
                        f"{categoria}/%",
                        self.ventana,
                    ),
                )

                usadas = {
                    row["imagen"].split("/")[-1]
                    for row in cur.fetchall()
                    if row.get("imagen")
                }

        candidatas = [f for f in archivos if f not in usadas]
        if not candidatas:
            candidatas = archivos  # fallback consciente

        elegida = random.choice(candidatas)

        print(
            f"[BG] categoria={categoria} usadas={len(usadas)} candidatas={len(candidatas)}"
        )

        return os.path.join(carpeta, elegida)
