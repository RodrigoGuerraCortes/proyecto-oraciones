#!/usr/bin/env python3
import os
import time
import json
import base64
import hashlib
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, urlencode

import requests
from dotenv import load_dotenv
from dotenv import set_key

ENV_PATH = ".env"

# TikTok endpoints
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# Server local (debe coincidir con el puerto al que apunta ngrok)
LOCAL_LISTEN_HOST = "0.0.0.0"
LOCAL_LISTEN_PORT = int(os.getenv("TIKTOK_LOCAL_PORT", "8080"))

# Margen para refrescar token antes de expirar
REFRESH_SAFETY_SECONDS = 90


def is_tiktok_sandbox() -> bool:
    return os.getenv("TIKTOK_ENV", "sandbox").lower() == "sandbox"

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _generate_pkce():
    """
    PKCE S256:
      code_verifier: string random
      code_challenge: BASE64URL(SHA256(code_verifier))
    """
    code_verifier = _b64url(secrets.token_bytes(32))
    code_challenge = _b64url(hashlib.sha256(code_verifier.encode("utf-8")).digest())
    return code_verifier, code_challenge


class CallbackState:
    def __init__(self):
        self.code = None
        self.error = None
        self.event = threading.Event()


def _load_env():
    load_dotenv(override=True)

    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI")

    if not client_key or not client_secret or not redirect_uri:
        raise RuntimeError(
            "Faltan variables en .env. Requeridas: "
            "TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REDIRECT_URI"
        )

    return client_key, client_secret, redirect_uri


def _get_scopes():
    # Ajusta si agregas más productos/scopes
    return ["video.upload", "video.publish", "user.info.basic"]


def _save_tokens_to_env(access_token: str, refresh_token: str | None, expires_in: int | None):
    # TikTok retorna expires_in en segundos
    now = int(time.time())
    expires_at = now + int(expires_in or 0)

    set_key(ENV_PATH, "TIKTOK_ACCESS_TOKEN", access_token)
    if refresh_token:
        set_key(ENV_PATH, "TIKTOK_REFRESH_TOKEN", refresh_token)
    if expires_in:
        set_key(ENV_PATH, "TIKTOK_ACCESS_TOKEN_EXPIRES_AT", str(expires_at))


def refresh_access_token() -> str:
    """
    Refresca access token usando refresh token (si existe).
    """
    client_key, client_secret, _redirect_uri = _load_env()
    refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")

    if not refresh_token:
        raise RuntimeError("No hay TIKTOK_REFRESH_TOKEN en .env. Requiere OAuth manual (primera vez).")

    payload = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=30)
    r.raise_for_status()

    resp = r.json()

    access_token = resp.get("access_token")
    refresh_token = resp.get("refresh_token")
    expires_in = resp.get("expires_in")

    if not access_token:
        raise RuntimeError(f"Respuesta inesperada refrescando token: {json.dumps(resp, ensure_ascii=False)}")

    _save_tokens_to_env(access_token, refresh_token, expires_in)
    return access_token


def get_access_token() -> str:
    """
    Devuelve access token válido:
      - si existe y no expira pronto -> retorna
      - si expira -> refresh
      - si no existe -> obliga OAuth manual (run_oauth_flow)
    """
    load_dotenv(override=True)
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    expires_at = os.getenv("TIKTOK_ACCESS_TOKEN_EXPIRES_AT")

    if access_token and expires_at:
        try:
            exp = int(float(expires_at))
            if int(time.time()) < (exp - REFRESH_SAFETY_SECONDS):
                return access_token
        except ValueError:
            pass

    # si hay refresh_token -> refrescar
    if os.getenv("TIKTOK_REFRESH_TOKEN"):
        return refresh_access_token()

    raise RuntimeError("No hay token válido. Ejecuta OAuth manual con run_oauth_flow().")


def exchange_code_for_tokens(code: str, code_verifier: str) -> str:
    client_key, client_secret, redirect_uri = _load_env()

    payload = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=30)
    r.raise_for_status()

    resp = r.json()
    access_token = resp.get("access_token")
    refresh_token = resp.get("refresh_token")
    expires_in = resp.get("expires_in")

    if not access_token:
        raise RuntimeError(f"Respuesta inesperada intercambiando code: {json.dumps(resp, ensure_ascii=False)}")

    _save_tokens_to_env(access_token, refresh_token, expires_in)
    return access_token


def run_oauth_flow() -> str:
    """
    Flujo completo:
      - genera PKCE
      - abre browser
      - levanta server local para /callback
      - captura code
      - intercambia por tokens
    """
    client_key, _client_secret, redirect_uri = _load_env()
    scopes = _get_scopes()

    code_verifier, code_challenge = _generate_pkce()
    state = _b64url(secrets.token_bytes(16))

    cb = CallbackState()

    # Asegura que el redirect_uri tenga path /callback recomendado
    # (Si tú lo configuraste como raíz, también funciona, pero esto es más limpio)
    ru = redirect_uri

    auth_params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": ",".join(scopes),
        "redirect_uri": ru,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = AUTH_URL + "?" + urlencode(auth_params)

    # HTTP handler para capturar el callback
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                parsed = urlparse(self.path)
                qs = parse_qs(parsed.query)

                # Validación básica de ruta: aceptamos /callback y /
                if parsed.path not in ("/callback", "/"):
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Not found")
                    return

                if "error" in qs:
                    cb.error = qs.get("error", ["unknown_error"])[0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"OAuth error received. You can close this tab.")
                    cb.event.set()
                    return

                code = qs.get("code", [None])[0]
                st = qs.get("state", [None])[0]

                if not code:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Missing code.")
                    return

                if st and st != state:
                    cb.error = "state_mismatch"
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"State mismatch.")
                    cb.event.set()
                    return

                cb.code = code

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"""
                    <html><body>
                    <h2>OK</h2>
                    <p>Authorization received. You can close this tab and return to the terminal.</p>
                    </body></html>
                    """
                )
                cb.event.set()

            except Exception as e:
                cb.error = str(e)
                cb.event.set()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Internal error")

        def log_message(self, format, *args):
            # Silenciar logs del server
            return

    # Levantar server en thread
    server = HTTPServer((LOCAL_LISTEN_HOST, LOCAL_LISTEN_PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    print("🌐 Abriendo navegador para login TikTok...")
    print(auth_url)
    webbrowser.open(auth_url)

    print("⏳ Esperando autorización... (callback HTTP)")
    cb.event.wait(timeout=240)

    # Cerrar server
    server.shutdown()
    server.server_close()

    if cb.error:
        raise RuntimeError(f"OAuth error: {cb.error}")
    if not cb.code:
        raise TimeoutError("No llegó el callback con code. Revisa redirect_uri, ngrok y puerto local.")

    print("✅ Code recibido. Intercambiando por tokens...")
    access_token = exchange_code_for_tokens(cb.code, code_verifier)

    print("🎉 Tokens guardados en .env (TIKTOK_ACCESS_TOKEN, TIKTOK_REFRESH_TOKEN, EXPIRES_AT)")
    return access_token


def main():
    # Si ya tienes refresh token, preferimos devolver token válido sin login.
    try:
        token = get_access_token()
        print("✅ Access token válido/actualizado desde refresh.")
        return
    except Exception:
        pass

    # Si no hay refresh token, hay que hacer login manual
    run_oauth_flow()


if __name__ == "__main__":
    main()
