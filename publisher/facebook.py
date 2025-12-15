from publisher.base import BasePublisher
from subir_video_facebook import subir_reel_facebook
from generar_descripcion import generar_descripcion
from zoneinfo import ZoneInfo

CL_TZ = ZoneInfo("America/Santiago")


class FacebookPublisher(BasePublisher):

    platform_code = "facebook"
    max_days_a_publicar = 2  # hoy + mañana (anti-spam)

    def publish_video(self, archivo, publicar_en, publication_id):
        """
        Publica un Reel en Facebook programado.
        Retorna el video_id (external_id).
        """

        # 1. Normalizar timezone (Chile)
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        # 2. Convertir a UNIX timestamp (Facebook REQUIREMENT)
        scheduled_publish_time = int(publicar_en.timestamp())

        # 3. Descripción
        descripcion = generar_descripcion(
            tipo="auto",
            hora_texto=publicar_en,
            archivo_texto=archivo,
            plataforma="facebook",
        )

        # 4. Subida (programada)
        return subir_reel_facebook(
            ruta_video=archivo,
            descripcion=descripcion,
            scheduled_publish_time=scheduled_publish_time
        )
