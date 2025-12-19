# generator/content/descripcion.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from generator.content.descriptions.youtube import generar_descripcion_youtube
from generator.content.descriptions.facebook import generar_descripcion_facebook
from generator.content.descriptions.instagram import generar_descripcion_instagram
from generator.content.descriptions.tiktok import generar_descripcion_tiktok
# Cargar variables del .env
load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def seleccionar_estilo_prompt(publication_id: int) -> int:
    return publication_id % 3

# =====================================================================
#   FUNCIÓN PRINCIPAL — AHORA MULTIPLATAFORMA
# =====================================================================
def generar_descripcion(
    *,
    tipo,
    hora_texto,
    plataforma="youtube",
    archivo_texto=None,
    texto_base=None,
    licence=None,
):

    """
    Genera una descripción optimizada según plataforma:
        - "youtube"
        - "facebook"
        - "instagram"
    """

    if plataforma == "youtube":
        return generar_descripcion_youtube(
                tipo=tipo,
                hora_texto=hora_texto,
                archivo_texto=archivo_texto,
                texto_base=texto_base,
                licence=licence,
            )
    elif plataforma == "facebook":
        return generar_descripcion_facebook(
                tipo=tipo,
                hora_texto=hora_texto,
                archivo_texto=archivo_texto,
                texto_base=texto_base,
            )
    elif plataforma == "instagram":
         return generar_descripcion_instagram(
                tipo=tipo,
                hora_texto=hora_texto,
                archivo_texto=archivo_texto,
                texto_base=texto_base,
            )
    elif plataforma == "tiktok":
        return generar_descripcion_tiktok(
                    tipo=tipo,
                    hora_texto=hora_texto,
                    archivo_texto=archivo_texto,
                    texto_base=texto_base,
                )

    else:
        raise ValueError(f"Plataforma no soportada: {plataforma}")





