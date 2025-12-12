#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# ==========================================================
# CARGAR .env
# ==========================================================
load_dotenv()

APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
ENV_FILE = ".env"


def update_env_var(key, value):
    """Actualiza o inserta una variable en el archivo .env."""
    lines = []
    found = False

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    with open(ENV_FILE, "w") as f:
        for line in lines:
            if line.startswith(key + "="):
                f.write(f"{key}={value}\n")
                found = True
            else:
                f.write(line)

        if not found:
            f.write(f"{key}={value}\n")

    print(f"✔ Variable actualizada en .env → {key}")


def generar_long_lived_token(short_token):
    """
    Convierte un token short-lived en un long-lived token (60 días)
    """
    print("\n🔄 Intercambiando Short-Lived Token por Long-Lived Token...")

    url = "https://graph.facebook.com/v17.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_token
    }

    r = requests.get(url, params=params)
    data = r.json()

    if "access_token" not in data:
        raise RuntimeError(f"Error generando Long-Lived Token: {data}")

    print("✔ Long-Lived Token obtenido correctamente.")
    return data["access_token"]


def obtener_page_token(long_token):
    """
    Usa el Long-Lived User Token para obtener:
    - PAGE_ID
    - PAGE_ACCESS_TOKEN
    """
    print("\n🔍 Obteniendo páginas administradas por el usuario...")

    url = "https://graph.facebook.com/v17.0/me/accounts"
    params = {"access_token": long_token}

    r = requests.get(url, params=params)
    data = r.json()

    if "data" not in data:
        raise RuntimeError(f"No fue posible obtener la lista de páginas: {data}")

    pages = data["data"]

    if len(pages) == 0:
        raise RuntimeError("Este usuario no administra ninguna página.")

    print(f"✔ {len(pages)} página(s) encontrada(s).")

    # Buscar tu página por nombre
    for page in pages:
        if page["name"] == "Oración Diaria 1 Minuto":
            print("\n🎯 Página encontrada: Oración Diaria 1 Minuto")
            return page["id"], page["access_token"]

    print("\n⚠ Página 'Oración Diaria 1 Minuto' no encontrada. Se usará la primera de la lista.")
    first = pages[0]
    return first["id"], first["access_token"]


def main():
    print("============================================")
    print(" 🔐 GENERACIÓN AUTOMÁTICA TOKEN FACEBOOK")
    print("============================================\n")

    if not APP_ID or not APP_SECRET:
        print("❌ ERROR: Debes definir FB_APP_ID y FB_APP_SECRET en tu archivo .env")
        return

    short_token = input("👉 Ingresa tu Short-Lived User Token (desde Graph API Explorer):\n\n> ").strip()

    if not short_token:
        print("❌ No ingresaste un token.")
        return

    try:
        long_token = generar_long_lived_token(short_token)
    except Exception as e:
        print(f"\n❌ Error obteniendo Long-Lived Token: {e}")
        return

    # Guardar long-lived token como usuario en .env
    update_env_var("FB_USER_ACCESS_TOKEN", long_token)

    try:
        page_id, page_token = obtener_page_token(long_token)
    except Exception as e:
        print(f"\n❌ Error obteniendo Page Token: {e}")
        return

    print("\n============================================")
    print(" ✔ RESULTADOS")
    print("============================================")
    print(f"PAGE_ID: {page_id}")
    print(f"PAGE_ACCESS_TOKEN: {page_token}\n")

    update_env_var("FB_PAGE_ID", page_id)
    update_env_var("FB_PAGE_ACCESS_TOKEN", page_token)

    print("\n🎉 PROCESO COMPLETADO")
    print("Tu .env contiene ahora los tokens correctos para automatizar Facebook.\n")


if __name__ == "__main__":
    main()
