# generator/v3/publications/crear_publications.py

from __future__ import annotations

from datetime import datetime, timedelta
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

from db.connection import get_connection
from generator.v3.publications.rules import VENTANAS
from generator.v3.publications.editorial_windows import (
    PLATFORM_REUSE_DAYS,
    GLOBAL_ANTISPAM_DAYS,
)

from db.repositories.channel_config_repo import get_channel_config


def _log_skip(reason: str, *, video_id, platform_id, publicar_en, extra=None):
    msg = (
        f"[EDITORIAL][SKIP] reason={reason} "
        f"video={video_id} "
        f"platform={platform_id} "
        f"fecha={publicar_en}"
    )
    if extra:
        msg += f" extra={extra}"
    print(msg)


def get_publication_strategy(channel_id: int) -> dict:
    cfg = get_channel_config(channel_id)
    strategy = cfg.get("publication_strategy")

    if not strategy:
        raise RuntimeError(
            f"channel {channel_id} no define publication_strategy"
        )

    return strategy


# ======================================================
# Reglas editoriales por plataforma (exposición de un video)
# ======================================================

EDITORIAL_RULES = {
    "short_oracion": {
        1: {"dias": 60, "max_reps": 1},
        2: {"dias": 30, "max_reps": 3},
        3: {"dias": 30, "max_reps": 3},
        4: {"dias": 7,  "max_reps": 1},
    },
    "long_salmo": {
        1: {"dias": 3650, "max_reps": 1},  # YouTube long
    }
}


ESTADOS_VIVOS = ("scheduled", "publishing", "published")

PLATFORM_CODE_TO_ID = {
    "youtube": 1,
    "facebook": 2,
    "instagram": 3,
    "tiktok": 4,
}

FORMAT_TO_TIPO = {
    "short_oracion": "short_oracion",
    "short_salmo": "short_salmo",
    "long_oracion_guiada": "long_oracion_guiada",
}


# ======================================================
# Public API
# ======================================================

def crear_publications(channel_id: int, dias: int = 7) -> List[Dict[str, Any]]:

    # --------------------------------------------------
    # 1. Configuración del canal (solo estrategia)
    # --------------------------------------------------
    channel_cfg = get_channel_config(channel_id)
    strategy = channel_cfg.get("publication_strategy")

    if not strategy:
        raise RuntimeError(
            f"channel {channel_id} no define publication_strategy"
        )

    print(f"[CREAR PUBLICATIONS] channel_id={channel_id} dias={dias}")
    print(f"[CREAR PUBLICATIONS] strategy={strategy}")

    # --------------------------------------------------
    # 2. Fechas base
    # --------------------------------------------------
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with get_connection() as conn:
        with conn.cursor() as cur:

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

            # videos disponibles
            cur.execute("""
                SELECT *
                FROM videos
                WHERE channel_id = %s
                  AND fecha_generado >= %s
                  AND activo = TRUE
                ORDER BY fecha_generado ASC
            """, (channel_id, bootstrap_date))
            videos = cur.fetchall()

    publicaciones_creadas: List[Dict[str, Any]] = []
    bootstrap_day = bootstrap_date.date()

    print(
        f"[DEBUG][VIDEOS] encontrados={len(videos)} "
        f"bootstrap_date={bootstrap_date}"
    )

    platform_ids = [
        PLATFORM_CODE_TO_ID[p]
        for p in strategy.keys()
        if p in PLATFORM_CODE_TO_ID
    ]

    # --------------------------------------------------
    # 3. Loop por día
    # --------------------------------------------------
    for dia_offset in range(dias):
        fecha_base = hoy + timedelta(days=dia_offset)

        dias_desde_bootstrap = (fecha_base.date() - bootstrap_day).days
        es_dia_olo = (dias_desde_bootstrap % 2 == 1)

        # --------------------------------------------------
        # 3.1 Slots efectivos del día (desde JSON)
        # --------------------------------------------------
        slots_del_dia = []
        slots_por_plataforma = Counter()

        for platform_code, platform_cfg in strategy.items():
            platform_id = PLATFORM_CODE_TO_ID.get(platform_code)
            if not platform_id:
                continue

            for slot_code, slot_cfg in platform_cfg["slots"].items():
                hora_str = slot_cfg["time"]
                format_cfg = slot_cfg["format"]

                # resolver format_code según paridad
                if es_dia_olo and "odd_day" in format_cfg:
                    format_code = format_cfg["odd_day"]
                elif not es_dia_olo and "even_day" in format_cfg:
                    format_code = format_cfg["even_day"]
                else:
                    format_code = format_cfg["default"]

                tipo = FORMAT_TO_TIPO.get(format_code)
                if not tipo:
                    continue

                hora, minuto = map(int, hora_str.split(":"))

                slot = {
                    "platform_id": platform_id,
                    "hora": hora,
                    "minuto": minuto,
                    "tipo": tipo,
                    "format_code": format_code,
                }

                print(
                    f"[DEBUG][SLOT] platform={platform_id} "
                    f"format={format_code} "
                    f"time={hora_str} "
                    f"tipo={tipo}"
                )

                slots_del_dia.append(slot)
                slots_por_plataforma[(platform_id, tipo)] += 1

        print(
            f"[DEBUG][SLOTS] fecha={fecha_base.date()} "
            f"total_slots={len(slots_del_dia)} "
            f"detalle={[(s['platform_id'], s['format_code']) for s in slots_del_dia]}"
        )

        # --------------------------------------------------
        # 3.2 Slots ya consumidos ese día
        # --------------------------------------------------
        consumidas_por_plataforma = _contar_publicaciones_del_dia_por_plataforma(
            channel_id,
            fecha_base,
            platform_ids,
        )

        # --------------------------------------------------
        # 3.3 Intentar llenar cada slot
        # --------------------------------------------------
        for s in slots_del_dia:
            platform_id = s["platform_id"]
            tipo = s["tipo"]

            key = (platform_id, tipo)
            slots_totales = slots_por_plataforma.get(key, 0)
            ya_consumidas = consumidas_por_plataforma.get(key, 0)

            if ya_consumidas >= slots_totales:
                continue

            publicar_en = fecha_base.replace(
                hour=s["hora"],
                minute=s["minuto"],
            )

            print(
                f"[DEBUG][TRY] platform={platform_id} "
                f"format={s['format_code']} "
                f"publicar_en={publicar_en}"
            )

            if _slot_ocupado(channel_id, platform_id, publicar_en):
                continue

            video = _buscar_video_valido(
                videos,
                publicar_en,
                s["format_code"],
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
                    "format_code": s["format_code"],
                })
                consumidas_por_plataforma[key] = ya_consumidas + 1

    return publicaciones_creadas




# ======================================================
# Selección de video (REFACTOR CRÍTICO)
# ======================================================

def _is_long_format(format_code: str) -> bool:
    return format_code.startswith("long_")


def _tipo_logico_desde_format(format_code: str) -> str:
    """
    Compatibilidad temporal con reglas legacy.
    """
    if format_code.startswith("long_"):
        return "long"
    return "short"

FORMAT_TO_VENTANA = {
    "short_oracion": "oracion",
    "short_salmo": "salmo",
}

def _buscar_video_valido(
    videos: List[Dict[str, Any]],
    publicar_en: datetime,
    format_code: str,
    channel_id: int,
    platform_id: int
) -> Optional[Dict[str, Any]]:

    is_long = _is_long_format(format_code)
    tipo_logico = _tipo_logico_desde_format(format_code)

    if is_long:
        print(
            f"[LONG][CHECK] buscando long "
            f"channel={channel_id} "
            f"platform={platform_id} "
            f"fecha={publicar_en}"
        )

    # --------------------------
    # Ventanas editoriales
    # --------------------------
    if not is_long:
        ventana_key = FORMAT_TO_VENTANA.get(format_code)
        if not ventana_key:
            return None

        ventana_slug = VENTANAS[ventana_key]["slug"]
        ventana_texto = VENTANAS[ventana_key]["texto"]
    else:
        ventana_slug = None
        ventana_texto = None

    dias_reuso_plataforma = PLATFORM_REUSE_DAYS.get(platform_id, 3)

    print(
        f"[DEBUG][VIDEOS] total_videos={len(videos)} "
        f"format_codes={set(v.get('format_code') for v in videos)}"
    )

    for video in videos:

        print(
           f"[DEBUG][VIDEO] id={video['id']} "
            f"tipo={video.get('tipo')} "
            f"format_code={video.get('format_code')} "
            f"archivo_ok={os.path.exists(video['archivo'])}"
        )

        # --------------------------
        # MATCH POR FORMAT (CLAVE)
        # --------------------------
        video_format = video.get("format_code")
        if video_format:
            if video_format != format_code:
                continue
        else:
            # Fallback legacy por tipo
            if video.get("tipo") != FORMAT_TO_TIPO.get(format_code):
                continue


        if is_long:
            print(
                f"[LONG][VIDEO] candidato id={video['id']} "
                f"archivo={os.path.basename(video['archivo'])}"
            )

        if not os.path.exists(video["archivo"]):
            continue

        # ==========================
        # LONG = evento único
        # ==========================
        if is_long:
            if _video_publicado_globalmente_reciente(
                channel_id,
                video["id"],
                publicar_en,
                dias=3650,
            ):
                _log_skip(
                    "GLOBAL_ANTISPAM",
                    video_id=video["id"],
                    platform_id=platform_id,
                    publicar_en=publicar_en,
                    extra={"dias": GLOBAL_ANTISPAM_DAYS},
                )
                continue

            print(f"[LONG][OK] seleccionado id={video['id']}")
            return video

        # ==========================
        # SHORTS (reglas existentes)
        # ==========================
        if _video_publicado_globalmente_reciente(
            channel_id,
            video["id"],
            publicar_en,
            GLOBAL_ANTISPAM_DAYS,
        ):
            print(f"[DEBUG][SKIP] global_antispam id={video['id']}")
            continue

        if _video_publicado_recientemente_en_plataforma(
            channel_id,
            video["id"],
            platform_id,
            publicar_en,
            dias_reuso_plataforma,
        ):
            _log_skip(
                "PLATFORM_REUSE",
                video_id=video["id"],
                platform_id=platform_id,
                publicar_en=publicar_en,
                extra={"dias": dias_reuso_plataforma},
            )
            continue

        if _slug_colision(video, publicar_en, ventana_slug, channel_id, platform_id):
            _log_skip(
                "SLUG_COLLISION",
                video_id=video["id"],
                platform_id=platform_id,
                publicar_en=publicar_en,
                extra={"ventana_horas": ventana_slug.total_seconds() / 3600},
            )
            continue

        if _texto_colision(video, publicar_en, ventana_texto, channel_id, platform_id):
            _log_skip(
                "TEXT_COLLISION",
                video_id=video["id"],
                platform_id=platform_id,
                publicar_en=publicar_en,
                extra={"ventana_horas": ventana_texto.total_seconds() / 3600},
            )
            continue

        if _excede_exposicion_editorial(
            channel_id,
            video["id"],
            platform_id,
            tipo_logico,
        ):
            rule = EDITORIAL_RULES.get(tipo_logico, {}).get(platform_id)
            _log_skip(
                "EDITORIAL_LIMIT",
                video_id=video["id"],
                platform_id=platform_id,
                publicar_en=publicar_en,
                extra=rule,
            )
            continue

        return video

    if is_long:
        print(
            f"[LONG][MISS] no se encontró long válido "
            f"channel={channel_id} "
            f"platform={platform_id} "
            f"fecha={publicar_en}"
        )

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

def _excede_exposicion_editorial(channel_id, video_id, platform_id, tipo) -> bool:
    rule = EDITORIAL_RULES.get(tipo, {}).get(platform_id)
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
                SELECT p.platform_id,  v.tipo, COUNT(*) AS total
                FROM publications p
                JOIN videos v ON v.id = p.video_id
                WHERE v.channel_id = %s
                  AND p.platform_id = ANY(%s)
                  AND p.estado IN {ESTADOS_VIVOS}
                  AND p.publicar_en >= %s
                  AND p.publicar_en < %s
                GROUP BY p.platform_id, v.tipo
            """, (channel_id, platform_ids, inicio, fin))
            return {
                (r["platform_id"], r["tipo"]): r["total"]
                for r in cur.fetchall()
            }

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
