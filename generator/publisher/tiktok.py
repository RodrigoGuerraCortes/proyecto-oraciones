from generator.publisher.base import BasePublisher
from generator.integrations.tiktok_api import (
    crear_contenedor_tiktok,
    subir_video_tiktok,
)
from generator.content.descripcion import generar_descripcion


class TikTokPublisher(BasePublisher):

    platform_code = "tiktok"
    allow_future_publication = False  # TikTok SANDBOX = inmediato

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
        # Descripción solo trazabilidad
        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            texto_base=texto_base,
            plataforma="tiktok",
        )

        print("\n===== TIKTOK SANDBOX UPLOAD =====")
        print(f"Archivo : {archivo}")
        print("Descripción (solo referencia):")
        print(descripcion)
        print("================================\n")

        publish_id, upload_url = crear_contenedor_tiktok(archivo)
        subir_video_tiktok(upload_url, archivo)

        return publish_id

    def preview_publication(
        self,
        publication_id,
        publicar_en,
        archivo,
        tipo,
        licencia,
        texto_base,
    ):
        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            texto_base=texto_base,
            plataforma="tiktok",
        )

        print("\n===== DRY RUN — TIKTOK =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print("Descripción (solo referencia):")
        print(descripcion)
        print("=============================\n")


        print("🎉 TikTok Sandbox upload completed successfully")
        print("ℹ️ Note: Videos uploaded in Sandbox do NOT appear in drafts or feed")