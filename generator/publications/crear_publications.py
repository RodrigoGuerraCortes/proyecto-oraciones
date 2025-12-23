from __future__ import annotations

from datetime import datetime, timedelta
import os
from collections import Counter
from typing import Any, Dict, List, Optional

from db.connection import get_connection
from generator.publications.rules import VENTANAS
from generator.publications.editorial_windows import (
    PLATFORM_REUSE_DAYS,
    GLOBAL_ANTISPAM_DAYS,
)

# ======================================================
# Reglas editoriales por plataforma (exposición de un video)
# ======================================================

EDITORIAL_RULES = {
    1: {"dias": 60, "max_reps": 1},    # YouTube
    2: {"dias": 30, "max_reps": 3},    # Facebook
    3: {"dias": 30, "max_reps": 3},    # Instagram
    4: {"dias": 7,  "max_reps": 1},    # TikTok
}

ESTADOS_VIVOS = ("scheduled", "publishing", "published")


# ======================================================
# Public API
# ======================================================

def crear_publications(channel_id: int, dias: int = 7) -> List[Dict[str, Any]]:

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Schedules activos
            cur.execute("""
                SELECT platform_id, hora, tipo
                FROM platform_schedules
                WHERE channel_id = %s
                  AND activo = true
                ORDER BY hora, platform_id
            """, (channel_id,))
            schedules = cur.fetchall()

            if not schedules:
                return []

            # bootstrap_date
            cur.execute("""
                SELECT value
                FROM system_config
                WHERE key = 'bootstrap_date'
            """)
            row = cur.fetchone()
            if not row:
                raise RuntimeError("bootstrap_date no definido")
            bootstrap_date = row["value"]

            # Inventario editorial
            cur.execute("""
                SELECT *
                FROM videos
                WHERE channel_id = %s
                  AND fecha_generado >= %s
                ORDER BY fecha_generado ASC
            """, (channel_id, bootstrap_date))
            videos = cur.fetchall()

    slots_por_plataforma = Counter(s["platform_id"] for s in schedules)
    publicaciones_creadas: List[Dict[str, Any]] = []

    for dia_offset in range(dias):
        fecha_base = hoy + timedelta(days=dia_offset)

        consumidas_por_plataforma = _contar_publicaciones_del_dia_por_plataforma(
            channel_id,
            fecha_base,
            list(slots_por_plataforma.keys()),
        )

        for s in schedules:
            platform_id = s["platform_id"]
            tipo = s["tipo"]

            slots_del_dia = slots_por_plataforma[platform_id]
            ya_consumidas = consumidas_por_plataforma.get(platform_id, 0)

            if ya_consumidas >= slots_del_dia:
                continue

            publicar_en = fecha_base.replace(
                hour=s["hora"].hour,
                minute=s["hora"].minute
            )

            if _slot_ocupado(channel_id, platform_id, publicar_en):
                continue

            video = _buscar_video_valido(
                videos,
                publicar_en,
                tipo,
                channel_id,
                platform_id,
            )

            if not video:
                continue

            if _insertar_publication(video["id"], platform_id, publicar_en):
                publicaciones_creadas.append({
                    "fecha": publicar_en,
                    "video": video["archivo"],
                    "platform": platform_id,
                    "tipo": tipo,
                })
                consumidas_por_plataforma[platform_id] = ya_consumidas + 1

    return publicaciones_creadas


# ======================================================
# Selección de video (REFACTOR CRÍTICO)
# ======================================================

def _buscar_video_valido(
    videos: List[Dict[str, Any]],
    publicar_en: datetime,
    tipo: str,
    channel_id: int,
    platform_id: int
) -> Optional[Dict[str, Any]]:

    ventana_slug = VENTANAS[tipo]["slug"]
    ventana_texto = VENTANAS[tipo]["texto"]

    dias_reuso_plataforma = PLATFORM_REUSE_DAYS.get(platform_id, 3)

    for video in videos:

        if video["tipo"] != tipo:
            continue

        if not os.path.exists(video["archivo"]):
            continue

        # 🔒 Anti-spam GLOBAL (muy corto)
        if _video_publicado_globalmente_reciente(
            channel_id,
            video["id"],
            publicar_en,
            GLOBAL_ANTISPAM_DAYS,
        ):
            continue

        # 📺 Reuso editorial POR PLATAFORMA
        if _video_publicado_recientemente_en_plataforma(
            channel_id,
            video["id"],
            platform_id,
            publicar_en,
            dias_reuso_plataforma,
        ):
            continue

        if _slug_colision(video, publicar_en, ventana_slug, channel_id, platform_id):
            continue

        if _texto_colision(video, publicar_en, ventana_texto, channel_id, platform_id):
            continue

        if _excede_exposicion_editorial(channel_id, video["id"], platform_id):
            continue

        return video

    return None


# ======================================================
# Reglas técnicas de colisión
# ======================================================

def _slug_colision(video, publicar_en, ventana, channel_id, platform_id) -> bool:
    slug = video["archivo"].split("__")[-1]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 1
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.platform_id = %s
                  AND p.estado IN {ESTADOS_VIVOS}
                  AND v.archivo LIKE %s
                  AND p.publicar_en BETWEEN %s AND %s
                LIMIT 1
            """, (
                channel_id,
                platform_id,
                f"%{slug}",
                publicar_en - ventana,
                publicar_en + ventana,
            ))
            return cur.fetchone() is not None


def _texto_colision(video, publicar_en, ventana, channel_id, platform_id) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 1
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.platform_id = %s
                  AND p.estado IN {ESTADOS_VIVOS}
                  AND v.texto_base = %s
                  AND p.publicar_en BETWEEN %s AND %s
                LIMIT 1
            """, (
                channel_id,
                platform_id,
                video["texto_base"],
                publicar_en - ventana,
                publicar_en + ventana,
            ))
            return cur.fetchone() is not None


# ======================================================
# Regla editorial de exposición
# ======================================================

def _excede_exposicion_editorial(channel_id, video_id, platform_id) -> bool:
    rule = EDITORIAL_RULES.get(platform_id)
    if not rule:
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) AS total
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.video_id = %s
                  AND p.platform_id = %s
                  AND p.estado IN {ESTADOS_VIVOS}
                  AND p.publicar_en >= NOW() - make_interval(days => %s)
            """, (
                channel_id,
                video_id,
                platform_id,
                rule["dias"],
            ))

            return cur.fetchone()["total"] >= rule["max_reps"]


# ======================================================
# Reglas críticas de slots
# ======================================================

def _contar_publicaciones_del_dia_por_plataforma(channel_id, fecha_base, platform_ids):
    inicio = fecha_base.replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=1)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT p.platform_id, COUNT(*) AS total
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.platform_id = ANY(%s)
                  AND p.estado IN {ESTADOS_VIVOS}
                  AND p.publicar_en >= %s
                  AND p.publicar_en < %s
                GROUP BY p.platform_id
            """, (channel_id, platform_ids, inicio, fin))
            return {r["platform_id"]: r["total"] for r in cur.fetchall()}


def _slot_ocupado(channel_id, platform_id, publicar_en) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 1
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.platform_id = %s
                  AND p.publicar_en = %s
                  AND p.estado IN {ESTADOS_VIVOS}
                LIMIT 1
            """, (channel_id, platform_id, publicar_en))
            return cur.fetchone() is not None


# ======================================================
# Inserción
# ======================================================

def _insertar_publication(video_id, platform_id, publicar_en) -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO publications (
                        video_id,
                        platform_id,
                        estado,
                        publicar_en
                    )
                    VALUES (%s, %s, 'scheduled', %s)
                """, (video_id, platform_id, publicar_en))
        return True
    except Exception:
        return False


# ======================================================
# Reglas de reutilización
# ======================================================

def _video_publicado_globalmente_reciente(channel_id, video_id, publicar_en, dias) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.video_id = %s
                  AND p.estado IN ('scheduled','publishing','published')
                  AND p.publicar_en >= %s
                LIMIT 1
            """, (channel_id, video_id, publicar_en - timedelta(days=dias)))
            return cur.fetchone() is not None


def _video_publicado_recientemente_en_plataforma(
    channel_id, video_id, platform_id, publicar_en, dias
) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.video_id = %s
                  AND p.platform_id = %s
                  AND p.estado IN ('scheduled','publishing','published')
                  AND p.publicar_en >= %s
                LIMIT 1
            """, (channel_id, video_id, platform_id, publicar_en - timedelta(days=dias)))
            return cur.fetchone() is not None
