from publisher.base import BasePublisher
from subir_video_youtube import subir_video_youtube
from generar_descripcion import generar_descripcion, generar_tags_from_descripcion
from datetime import timezone
from zoneinfo import ZoneInfo

CL_TZ = ZoneInfo("America/Santiago")


class YouTubePublisher(BasePublisher):

    platform_code = "youtube"
    max_days_a_publicar = 7  # YouTube tolera batch grande

    def publish_video(self, archivo, publicar_en, publication_id):

        # 1. Asignar timezone Chile si viene naive desde la BD
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        # 2. Convertir a UTC (formato correcto para YouTube)
        publish_at = publicar_en.astimezone(timezone.utc).isoformat()

        # 3. Metadata
        titulo_base = archivo.split("/")[-1].replace(".mp4", "")
        titulo = f"{titulo_base.replace('_', ' ').title()} — 1 minuto 🙏✨"

        descripcion = generar_descripcion(
            tipo="auto",
            hora_texto=publicar_en,  # Chile para texto humano
            archivo_texto=archivo,
            plataforma="youtube"
        )

        tags = generar_tags_from_descripcion(descripcion)

        # 4. Subida
        return subir_video_youtube(
            ruta=archivo,
            titulo=titulo,
            descripcion=descripcion,
            tags=tags,
            privacidad="private",
            publish_at=publish_at
        )
