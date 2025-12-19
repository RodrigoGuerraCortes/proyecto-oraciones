# generator/publisher/youtube.py

from datetime import timezone
from zoneinfo import ZoneInfo

from generator.publisher.base import BasePublisher
from generator.integrations.youtube_api import upload_video
from generator.content.tags import generar_tags_from_descripcion
from generator.content.descripcion import generar_descripcion
from generator.content.titulo import construir_titulo_desde_archivo

CL_TZ = ZoneInfo("America/Santiago")


class YouTubePublisher(BasePublisher):

    platform_code = "youtube"
    allow_future_publication = True
    max_days_a_publicar = 1

    # -------------------------------------------------
    # PUBLICACIÓN REAL
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
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        publish_at = publicar_en.astimezone(timezone.utc).isoformat()

        titulo = construir_titulo_desde_archivo(archivo)

        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            texto_base=texto_base,
            plataforma="youtube",
            licence=licencia,
        )

        tags = generar_tags_from_descripcion(descripcion)

        # 🔍 LOG EXPLÍCITO (ANTES DE SUBIR)
        print("\n===== YOUTUBE UPLOAD =====")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print(f"PublishAt UTC : {publish_at}")
        print(f"Título        : {titulo}")
        print("Descripción:")
        print(descripcion)
        print("Tags:")
        print(tags)
        print("==========================\n")

        return upload_video(
            ruta=archivo,
            titulo=titulo,
            descripcion=descripcion,
            tags=tags,
            privacidad="private",
            publish_at=publish_at,
        )

    # -------------------------------------------------
    # DRY RUN / PREVIEW
    # -------------------------------------------------
    def preview_publication(
        self,
        publication_id,
        publicar_en,
        archivo,
        tipo,
        licencia,
        texto_base,
    ):
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        publish_at = publicar_en.astimezone(timezone.utc).isoformat()

        titulo = construir_titulo_desde_archivo(archivo)

        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            texto_base=texto_base,
            plataforma="youtube",
            licence=licencia,
        )

        tags = generar_tags_from_descripcion(descripcion)

        print("\n===== DRY RUN — YOUTUBE =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print(f"PublishAt UTC : {publish_at}")
        print(f"Título        : {titulo}")
        print("Descripción:")
        print(descripcion)
        print("Tags:")
        print(tags)
        print("============================\n")
