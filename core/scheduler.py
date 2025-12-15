from datetime import datetime, timedelta, time
from db.connection import get_connection


VENTANA_DIAS = 7  # cuántos días hacia adelante planificar


def generar_publicaciones_youtube(channel_id: int):
    """
    Genera publications futuras para YouTube usando platform_schedules.
    Idempotente.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            # 1. Obtener platform_id de YouTube
            cur.execute("""
                SELECT id FROM platforms WHERE code = 'youtube'
            """)
            row = cur.fetchone()
            if not row:
                raise RuntimeError("Platform youtube no existe")
            platform_id = row[0]

            # 2. Obtener schedules activos
            cur.execute("""
                SELECT hora, tipo
                FROM platform_schedules
                WHERE platform_id = %s AND activo = true
                ORDER BY hora
            """, (platform_id,))
            schedules = cur.fetchall()

            if not schedules:
                print("[SCHEDULER] No hay schedules activos para YouTube")
                return

            ahora = datetime.now()

            for dia_offset in range(VENTANA_DIAS):
                fecha = (ahora + timedelta(days=dia_offset)).date()

                for hora, tipo in schedules:
                    publicar_en = datetime.combine(fecha, hora)

                    # solo futuro
                    if publicar_en <= ahora:
                        continue

                    # 3. ¿Ya existe publication?
                    cur.execute("""
                        SELECT 1
                        FROM publications
                        WHERE platform_id = %s
                          AND publicar_en = %s
                    """, (platform_id, publicar_en))

                    if cur.fetchone():
                        continue  # idempotencia

                    # 4. Elegir video (simple por ahora)
                    cur.execute("""
                        SELECT id
                        FROM videos
                        WHERE channel_id = %s
                          AND tipo = %s
                        ORDER BY fecha_generado ASC
                        LIMIT 1
                    """, (channel_id, tipo))

                    video = cur.fetchone()
                    if not video:
                        print(f"[SCHEDULER] No hay video tipo={tipo}")
                        continue

                    video_id = video[0]

                    # 5. Insertar publication
                    cur.execute("""
                        INSERT INTO publications (
                            video_id,
                            platform_id,
                            estado,
                            publicar_en
                        ) VALUES (%s, %s, 'scheduled', %s)
                    """, (video_id, platform_id, publicar_en))

                    print(
                        f"[SCHEDULER] YouTube scheduled → "
                        f"{publicar_en} | video={video_id}"
                    )

        conn.commit()
