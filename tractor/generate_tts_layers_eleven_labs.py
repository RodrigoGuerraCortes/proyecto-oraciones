import requests
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ======================
# CONFIGURACIÓN
# ======================

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ ELEVENLABS_API_KEY no está definida")

VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian
MODEL_ID = "eleven_v3"

INPUT_DIR = Path(
    "/mnt/storage/assets/texts/canal_catolico_01/tractores/oracion_para_dormir"
)

OUTPUT_DIR = Path(
    "/mnt/storage/generated/canal_catolico_01/longs/tractores/oracion_para_dormir/audio"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Content-Type": "application/json",
    "xi-api-key": API_KEY,
}

VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.08,
}

# ======================
# UTILIDADES INTERNAS
# ======================

def split_paragraphs(text: str):
    return [p.strip() for p in text.split("\n\n") if p.strip()]

def call_elevenlabs(text: str) -> bytes:
    payload = {
        "model_id": MODEL_ID,
        "text": text,
        "voice_settings": VOICE_SETTINGS,
    }

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    response = requests.post(url, headers=HEADERS, json=payload)

    if not response.ok:
        raise RuntimeError(response.text)

    return response.content

# ======================
# PROCESO PRINCIPAL
# ======================

def create_audio_eleven_lab():
    print("🎧 Generador de layers TTS iniciado")
    print(f"📂 Leyendo textos desde: {INPUT_DIR}")

    global_index = 1

    for txt_file in sorted(INPUT_DIR.glob("*.txt")):
        print(f"\n📄 Procesando archivo: {txt_file.name}")

        if txt_file.name != "08_cierre_espiritual_suave.txt":
            continue

        base_name = txt_file.stem
        content = txt_file.read_text(encoding="utf-8")
        paragraphs = split_paragraphs(content)

        for layer_index, paragraph in enumerate(paragraphs, start=1):
            filename = f"{global_index:04d}_{base_name}_{layer_index:02d}.mp3"
            output_path = OUTPUT_DIR / filename

            text_for_tts = f"[calm]\n{paragraph}"

            print(f"  🎙 Generando layer: {filename}")
            audio_bytes = call_elevenlabs(text_for_tts)
            output_path.write_bytes(audio_bytes)

            global_index += 1

    print("\n✅ Generación completada.")


