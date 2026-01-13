# entrypoint.py

import argparse
import uuid
import os
import sys
from dotenv import load_dotenv

from config.config_resolver import resolver_config
from engine.engines.registry import ENGINE_REGISTRY
from storage.output_resolver import resolve_output_path
from generator.selector_texto import elegir_texto
from tractor.fase_1_5_tts_layers import generar_tts_layers
from tractor.fase_1_6_expandir_tractor import expandir_tractor
from tractor.render_text_layers import render_layers_from_config
from tractor.generate_tts_layers_eleven_labs import create_audio_eleven_lab

load_dotenv()


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline v3 – Generación de videos (genérico)"
    )

    parser.add_argument(
        "--channel",
        type=int,
        required=True,
        help="ID del canal",
    )

    parser.add_argument(
        "--format",
        type=str,
        required=True,
        help="Código de formato (ej: short_oracion, short_salmo, long_guiado)",
    )

    parser.add_argument(
        "--text",
        type=str,
        required=False,
        help="Archivo de texto a usar (filename o path relativo según engine)",
    )

    parser.add_argument(
        "--out",
        type=str,
        required=False,
        help="Ruta del archivo de salida (.mp4) (opcional, solo para override/manual)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Modo test (duraciones mínimas)",
    )

    parser.add_argument(
        "--force-tts",
        action="store_true",
        help="Forzar TTS (override config)",
    )

    parser.add_argument(
        "--tractor",
        type=str,
        help="Nombre del tractor a procesar (solo para engine long_tractor)",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    args = parse_args()

    # ---------------------------------------------------------
    # Resolver config (UNA sola vez)
    # ---------------------------------------------------------
    resolved_config = resolver_config(
        channel_id=args.channel,
        format_code=args.format,
        tractor=args.tractor if args.tractor else None,
    )

    print("[Entrypoint] Resolved config :", resolved_config)

    print("[Entrypoint] Resolved config Identity :", resolved_config['identity']['code'])

    format_cfg = resolved_config["format"]
    engine_code = format_cfg.get("engine")
    format_type = format_cfg.get("type")

    print("[Entrypoint] Audio Music Path:", resolved_config["audio"]["music"]["base_path"])
    
    music_path = resolved_config["audio"]["music"]["base_path"]

    if not engine_code:
        raise RuntimeError(
            f"El formato '{args.format}' no define 'engine' en la config"
        )

    generator_fn = ENGINE_REGISTRY.get(engine_code)

    if not generator_fn:
        raise RuntimeError(
            f"Engine '{engine_code}' no registrado en ENGINE_REGISTRY"
        )

    video_id = str(uuid.uuid4())
    video_id_short = str(video_id).split("-")[0]
     
    print("[Entrypoint] Resolve Config:", resolved_config)
    print("[Entrypoint] Base Path Text:", resolved_config["content"]["base_path"])

    # 3. Resolver paths
    text_path, slug, texto = elegir_texto(
        content_base_path=resolved_config["content"]["base_path"],
        tipo=resolved_config["format"]["code"],
        archivo_forzado=args.text,
    )

    print("[Entrypoint] Resolved text path:", text_path)
    print("[Entrypoint] Resolved slug:", slug)

    output_path = resolve_output_path(
        override_out=args.out,
        channel_code=resolved_config["identity"]["code"],
        format_type=resolved_config["format"]["type"],
        video_id=video_id_short,
        slug=slug,
    )

    print("[Entrypoint] Resolved output path:", output_path)

    print("[ENTRYPOINT V3]")
    print(" - channel_id:", args.channel)
    print(" - format_code:", args.format)
    print(" - format_type:", format_type)
    print(" - engine:", engine_code)
    print(" - text:", text_path)
    print(" - output:", output_path)
    print(" - test:", args.test)
    print(" - force_tts:", args.force_tts)
    print(" - video_id:", video_id)


    print("[ENTRYPOINT] Config completa:", format_type)


    #if args.format == "long_tractor_oracion" and args.test:


        #RENDER DE LAYERS DE TEXTO A PNG
        #print("[ENTRYPOINT] Ejecutando FASE A: render de capas de texto")
        #render_layers_from_config(resolved_config)
        #return
#
#  
        #GENERACION DE MP3 TTS PARA CADA LAYER
        #Se ocuparan audos de elevenLabs, tts queda deshabilitado
        #print("[ENTRYPOINT] Forzando TTS según flag --force-tts")
        #create_audio_eleven_lab(resolved_config["content"]["base_path"], resolved_config["audio"]["audio_layers_path"], resolved_config["content"]["tts_prompt"])
        #return

        #GENERACION DE AUDIO FINAL EXPANDIENDO EL TRACTOR 
        #print("[ENTRYPOINT] Ejecutando FASE 1.6: expansión de tractor")
        #expandir_tractor(
        #    resolved_config=resolved_config,
        #    layers_path=resolved_config["content"]["layers_path"],
        #    audio_path=resolved_config["audio"]["audio_layers_path"],
        #    output_sequence_path=resolved_config["sequence_path"],
        #)
#
        #return
    # ---------------------------------------------------------
    # Ejecución del engine (GENÉRICA)
    # ---------------------------------------------------------
    generator_fn(
        resolved_config=resolved_config,
        text_path=text_path,
        output_path=output_path,
        video_id=video_id,
        channel_id=args.channel,
        modo_test=args.test,
        force_tts=True if args.force_tts else None,
        music_path=music_path,
    )

    print("[V3] Video generado correctamente")


if __name__ == "__main__":
    main()
