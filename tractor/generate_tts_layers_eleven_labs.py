import requests
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# ======================
# CONFIGURACIÓN
# ======================

API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ ELEVENLABS_API_KEY no está definida")

VOICE_ID = "RXFZiXt45hSwYjWAb0d5"  # VOZ 1 - GENERADA PARA EL CANAL
MODEL_ID = "eleven_v3"

#INPUT_DIR = Path(
#    "/mnt/storage/assets/texts/canal_catolico_01/tractores/oracion_poderosa_salmo_91"
#)

#OUTPUT_DIR = Path(
#    "/mnt/storage/generated/canal_catolico_01/longs/tractores/oracion_poderosa_salmo_91/audio"
#)


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

def create_audio_eleven_lab(input_dir: Path, output_dir: Path, tts_prompt: dict):
    print("🎧 Generador de layers TTS iniciado")

    INPUT_DIR = Path(input_dir)
    OUTPUT_DIR = Path(output_dir)

    print(f"📂 Leyendo textos desde: {INPUT_DIR}")
    print(f"📂 Generando audios en: {OUTPUT_DIR}")



    global_index = 1

    #PROMPTS = tts_prompt 
    #[{'01_entrada_y_transicion_al_descanso': '[very calm, soft, slow pace, warm, reassuring, spiritual, bedtime tone]'}, {'02_oracion_de_entrega_del_dia': '[gentle, intimate, slow, sincere, comforting, reflective, calm authority]'}, {'03_oracion_repetitiva_suave_ciclo_1': '[very soft, slow, steady, minimal emotion, meditative, sleep-inducing]'}, {'04_oracion_repetitiva_suave_ciclo_2': '[very soft, slow, steady, minimal emotion, meditative, sleep-inducing]'}, {'05_oracion_repetitiva_suave_ciclo_3': '[very soft, slow, steady, minimal emotion, meditative, sleep-inducing]'}, {'06_oracion_repetitiva_suave_ciclo_4': '[very soft, slow, steady, minimal emotion, meditative, sleep-inducing]'}, {'07_oracion_repetitiva_suave_ciclo_5': '[very soft, slow, steady, minimal emotion, meditative, sleep-inducing]'}, {'08_cierre_espiritual_suave': '[extremely calm, very slow, peaceful, low energy, whisper-like, safe and warm]'}, {'09_silencio_guiado': '[barely audible, very slow, minimal presence, guiding silence]'}]

    PROMPTS = {}

    for item in tts_prompt:
        PROMPTS.update(item)


    for txt_file in sorted(INPUT_DIR.glob("*.txt")):
        print(f"\n📄 Procesando archivo: {txt_file.name}")

        #if txt_file.name != "bloque_4_cierre_suave.txt":
        #    continue

        base_name = txt_file.stem
        content = txt_file.read_text(encoding="utf-8")
        paragraphs = split_paragraphs(content)

        for layer_index, paragraph in enumerate(paragraphs, start=1):
            filename = f"{global_index:04d}_{base_name}_{layer_index:02d}.mp3"
            output_path = OUTPUT_DIR / filename

            #text_for_tts = f"{paragraph}"


            prompt = PROMPTS.get(base_name, "")
            text_for_tts = f"{prompt}\n{paragraph}"

            print("[TTS ELEVEN LABS] Ejecutando PROMPT", text_for_tts)


            print(f"  🎙 Generando layer: {filename}")
            audio_bytes = call_elevenlabs(text_for_tts)
            output_path.write_bytes(audio_bytes)

            global_index += 1

    print("\n✅ Generación completada.")


