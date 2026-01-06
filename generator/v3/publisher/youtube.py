# generator/v3/publisher/youtube.py

from datetime import timezone
from zoneinfo import ZoneInfo

from generator.v3.publisher.base import BasePublisher
from generator.v3.integrations.youtube_api import upload_video

from generator.v3.generator.integrations.titulo import construir_titulo
from generator.v3.generator.integrations.descripcion import generar_descripcion
from generator.v3.generator.integrations.tags import generar_tags_from_descripcion


CL_TZ = ZoneInfo("America/Santiago")


class YouTubePublisher(BasePublisher):

    platform_code = "youtube"
    allow_future_publication = True
    max_days_a_publicar = 1

    print("[YOUTUBE PUBLISHER] Initialized")
    print(f"[YOUTUBE PUBLISHER] Timezone set to {CL_TZ}")
    print(f"[YOUTUBE PUBLISHER] Max days to schedule: {max_days_a_publicar}")

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
        editorial_cfg,
        channel_config,
    ):
        # -----------------------------
        # Timezone handling
        # -----------------------------
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        publish_at = publicar_en.astimezone(timezone.utc).isoformat()

        # -----------------------------
        # Editorial (YA RESUELTA)
        # -----------------------------
        tipo_cfg = editorial_cfg["tipo_cfg"]

        # -----------------------------
        # Título
        # -----------------------------
        titulo = construir_titulo(
            archivo=archivo,
            tipo=tipo,
            duracion=tipo_cfg.get("duracion", "1 minuto"),
            emoji=tipo_cfg.get("emoji", "🙏"),
        )

        # -----------------------------
        # Descripción
        # -----------------------------
        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="youtube",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        # -----------------------------
        # Tags (derivados de descripción)
        # -----------------------------
        tags = generar_tags_from_descripcion(descripcion)

        # -----------------------------
        # LOG EXPLÍCITO
        # -----------------------------
        print("\n===== YOUTUBE UPLOAD =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print(f"PublishAt UTC : {publish_at}")
        print(f"Tipo          : {tipo}")
        print(f"Título        : {titulo}")
        print("Descripción:")
        print(descripcion)
        print("Tags:")
        print(tags)
        print("==========================\n")

        # -----------------------------
        # Upload a YouTube
        # -----------------------------
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
        # -----------------------------
        # Timezone handling
        # -----------------------------
        if publicar_en.tzinfo is None:
            publicar_en = publicar_en.replace(tzinfo=CL_TZ)

        publish_at = publicar_en.astimezone(timezone.utc).isoformat()

        # -----------------------------
        # Editorial (YA RESUELTA)
        # -----------------------------
        tipo_cfg = editorial_cfg["tipo_cfg"]

        # -----------------------------
        # Título
        # -----------------------------
        titulo = construir_titulo(
            archivo=archivo,
            tipo=tipo,
            duracion=tipo_cfg.get("duracion", "1 minuto"),
            emoji=tipo_cfg.get("emoji", "🙏"),
        )

        # -----------------------------
        # Descripción
        # -----------------------------
        descripcion = generar_descripcion(
            tipo=tipo,
            publicar_en=publicar_en,
            texto_base=texto_base,
            plataforma="youtube",
            licence=licencia,
            editorial_cfg=editorial_cfg,
        )

        # -----------------------------
        # Tags
        # -----------------------------
        tags = generar_tags_from_descripcion(descripcion)

        # -----------------------------
        # OUTPUT DRY RUN
        # -----------------------------
        print("\n===== DRY RUN — YOUTUBE =====")
        print(f"Publication ID: {publication_id}")
        print(f"Archivo       : {archivo}")
        print(f"Publicar en   : {publicar_en}")
        print(f"PublishAt UTC : {publish_at}")
        print(f"Tipo          : {tipo}")
        print(f"Título        : {titulo}")
        print("Descripción:")
        print(descripcion)
        print("Tags:")
        print(tags)
        print("============================\n")
