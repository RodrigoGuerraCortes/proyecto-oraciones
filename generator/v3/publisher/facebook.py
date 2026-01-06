# generator/v3/publisher/facebook.py
from datetime import timezone
from zoneinfo import ZoneInfo

from generator.v3.publisher.base import BasePublisher
from generator.v3.integrations.facebook_api import subir_reel_facebook
from generator.v3.generator.integrations.descripcion import generar_descripcion

CL_TZ = ZoneInfo("America/Santiago")


class FacebookPublisher(BasePublisher):

    platform_code = "facebook"
    allow_future_publication = True
    max_days_a_publicar = 5

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
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        unix_time = int(publicar_en.timestamp())

        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="facebook",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        print("\n===== FACEBOOK REEL UPLOAD =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en} (unix={unix_time})")
        print("Descripción:")
        print(descripcion)
        print("================================\n")

        return subir_reel_facebook(
            ruta_video=archivo,
            descripcion=descripcion,
            scheduled_publish_time=unix_time,
        )

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
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="facebook",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        print("\n===== DRY RUN — FACEBOOK =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print("Descripción:")
        print(descripcion)
        print("==============================\n")
