from publisher.base import BasePublisher
from generar_descripcion import generar_descripcion
from zoneinfo import ZoneInfo

from subir_video_instagram import (
    subir_video_cloudinary,
    crear_contenedor_instagram,
    esperar_media_listo,
    programar_reel_instagram,
)

CL_TZ = ZoneInfo("America/Santiago")


class InstagramPublisher(BasePublisher):

    platform_code = "instagram"
    max_days_a_publicar = 1  # 🔥 SOLO HOY

    def publish_video(self, archivo, publicar_en, publication_id):
        """
        Publica un Reel en Instagram.
        Retorna creation_id como external_id.
        """

        # 1️⃣ Normalizar timezone (Chile)
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        # 2️⃣ Descripción optimizada IG
        descripcion = generar_descripcion(
            tipo="auto",
            hora_texto=publicar_en,
            archivo_texto=archivo,
            plataforma="instagram",
        )

        # 3️⃣ Instagram requiere UNIX timestamp
        publish_time_unix = int(publicar_en.timestamp())

        # 4️⃣ Subir a Cloudinary
        video_url = subir_video_cloudinary(archivo)

        # 5️⃣ Crear contenedor IG
        creation_id = crear_contenedor_instagram(
            video_url=video_url,
            descripcion=descripcion
        )

        # 6️⃣ Esperar procesamiento
        esperar_media_listo(creation_id)

        # 7️⃣ Publicar (en el momento indicado por tu scheduler)
        programar_reel_instagram(
            creation_id=creation_id,
            publish_time_unix=publish_time_unix
        )

        # 8️⃣ Retornar external_id
        return creation_id
