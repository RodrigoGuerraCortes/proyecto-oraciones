# publisher/instagram.py

from zoneinfo import ZoneInfo

from publisher.base import BasePublisher
from integrations.instagram_api import (
    subir_video_cloudinary,
    crear_contenedor_instagram,
    esperar_media_listo,
    publicar_reel_instagram,
)
from generator.integrations.descripcion import generar_descripcion

CL_TZ = ZoneInfo("America/Santiago")


class InstagramPublisher(BasePublisher):

    platform_code = "instagram"
    allow_future_publication = False  # cron manda

    def publish_video(
        self,
        *,
        archivo,
        publicar_en,
        publication_id,
        tipo,
        licencia,
        texto_base,
        editorial_cfg,
        channel_config,
    ):
        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="instagram",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        print("\n===== INSTAGRAM REEL UPLOAD =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print("Descripción:")
        print(descripcion)
        print("================================\n")

        video_url = subir_video_cloudinary(archivo)
        creation_id = crear_contenedor_instagram(video_url, descripcion)
        esperar_media_listo(creation_id)
        publicar_reel_instagram(creation_id)

        return creation_id

    def preview_publication(
        self,
        *,
        publication_id,
        publicar_en,
        archivo,
        tipo,
        licencia,
        texto_base,
        editorial_cfg,
        channel_config,
    ):
        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="instagram",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        print("\n===== DRY RUN — INSTAGRAM =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print("Descripción:")
        print(descripcion)
        print("==============================\n")
