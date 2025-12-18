from __future__ import annotations

from datetime import datetime, timedelta
import os
from collections import Counter
from typing import Any, Dict, List, Optional

from db.connection import get_connection
from generator.publications.rules import VENTANAS


# ======================================================
# Reglas editoriales por plataforma (exposición de un video)
# ======================================================

EDITORIAL_RULES = {
    # platform_id : { dias, max_reps }
    1: {"dias": 60, "max_reps": 1},    # YouTube
    2: {"dias": 30, "max_reps": 3},    # Facebook
    3: {"dias": 30, "max_reps": 3},    # Instagram
    4: {"dias": 7,  "max_reps": 999},  # TikTok
}

ESTADOS_VIVOS = ("scheduled", "publishing", "published")


# ======================================================
# Public API
# ======================================================

def crear_publications(channel_id: int, dias: int = 7) -> List[Dict[str, Any]]:
    """
    Genera publications para N días usando:
    - platform_schedules (capacidad diaria por plataforma = #slots definidos)
    - videos (inventario editorial)
    - reglas técnicas anti-colisión (slug/texto por plataforma)
    - reglas editoriales por plataforma (máx repeticiones por ventana)
    - regla CRÍTICA: una plataforma NO publica más de sus slots definidos por día
      (legacy-safe: si el día ya tiene publicaciones legacy, cuentan para el cupo)
    """

    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with get_connection() as conn:
        with conn.cursor() as cur:

            # 1️⃣ Schedules activos
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
                raise RuntimeError("bootstrap_date no definido en system_config")
            bootstrap_date = row["value"]

            # 2️⃣ Inventario editorial
            cur.execute("""
                SELECT *
                FROM videos
                WHERE channel_id = %s
                  AND fecha_generado >= %s
                ORDER BY fecha_generado DESC
            """, (channel_id, bootstrap_date))
            videos = cur.fetchall()

    # Capacidad diaria por plataforma = cantidad de schedules para esa plataforma
    slots_por_plataforma = Counter(s["platform_id"] for s in schedules)

    publicaciones_creadas: List[Dict[str, Any]] = []

    for dia_offset in range(dias):
        fecha_base = hoy + timedelta(days=dia_offset)

        # Optimizador: para cada día contamos una vez el consumo por plataforma
        consumidas_por_plataforma = _contar_publicaciones_del_dia_por_plataforma(
            channel_id=channel_id,
            fecha_base=fecha_base,
            platform_ids=list(slots_por_plataforma.keys()),
        )

        for s in schedules:
            platform_id = s["platform_id"]
            tipo = s["tipo"]

            # ✅ Regla crítica (cupos diarios): legacy y nuevos cuentan igual
            slots_del_dia = int(slots_por_plataforma[platform_id])
            ya_consumidas = int(consumidas_por_plataforma.get(platform_id, 0))
            if ya_consumidas >= slots_del_dia:
                continue

            publicar_en = fecha_base.replace(
                hour=s["hora"].hour,
                minute=s["hora"].minute
            )

            # ✅ Regla crítica adicional: no duplicar EXACTAMENTE el slot (platform + datetime)
            # Esto evita que, aunque haya cupo, se inserte donde ya existe un row.
            if _slot_ocupado(channel_id, platform_id, publicar_en):
                continue

            video = _buscar_video_valido(
                videos=videos,
                publicar_en=publicar_en,
                tipo=tipo,
                channel_id=channel_id,
                platform_id=platform_id
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
                # Importante: si insertamos, consumimos 1 cupo diario para esa plataforma
                consumidas_por_plataforma[platform_id] = ya_consumidas + 1

    return publicaciones_creadas


# ======================================================
# Selección de video
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

    for video in videos:

        if video["tipo"] != tipo:
            continue

        if not os.path.exists(video["archivo"]):
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

def _slug_colision(video: Dict[str, Any], publicar_en: datetime, ventana: timedelta, channel_id: int, platform_id: int) -> bool:
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
                publicar_en + ventana
            ))
            return cur.fetchone() is not None


def _texto_colision(video: Dict[str, Any], publicar_en: datetime, ventana: timedelta, channel_id: int, platform_id: int) -> bool:
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
                publicar_en + ventana
            ))
            return cur.fetchone() is not None


# ======================================================
# Regla editorial de exposición (por video)
# ======================================================

def _excede_exposicion_editorial(channel_id: int, video_id: str, platform_id: int) -> bool:
    rule = EDITORIAL_RULES.get(platform_id)
    if not rule:
        return False

    dias = int(rule["dias"])
    max_reps = int(rule["max_reps"])

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
            """, (channel_id, video_id, platform_id, dias))

            total = cur.fetchone()["total"]

    return int(total) >= max_reps


# ======================================================
# Reglas críticas: cupos diarios y slot único
# ======================================================

def _contar_publicaciones_del_dia_por_plataforma(
    channel_id: int,
    fecha_base: datetime,
    platform_ids: List[int],
) -> Dict[int, int]:
    """
    Cuenta publicaciones vivas en el día por plataforma.
    Esto es legacy-safe: si había publicaciones a horas antiguas,
    igual se consideran para el cupo del día.
    """
    if not platform_ids:
        return {}

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

            rows = cur.fetchall()

    return {int(r["platform_id"]): int(r["total"]) for r in rows}


def _slot_ocupado(channel_id: int, platform_id: int, publicar_en: datetime) -> bool:
    """
    Retorna True si ya existe una publication viva en ese slot exacto
    (mismo channel, misma plataforma, mismo publicar_en).
    """
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
# Insert publication
# ======================================================

def _insertar_publication(video_id: str, platform_id: int, publicar_en: datetime) -> bool:
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
