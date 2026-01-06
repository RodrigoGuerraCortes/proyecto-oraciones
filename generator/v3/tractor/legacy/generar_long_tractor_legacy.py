import os
import uuid

from moviepy.editor import (
    ImageClip,
    CompositeAudioClip,
    concatenate_audioclips,
)

from generator.v3.adapter.audio_fingerprint_adapter import resolver_audio_y_fingerprint_v3
from generator.v3.adapter.audio_tractor_adapter import crear_audio_tractor_v3
from generator.v3.adapter.fondo_pool_adapter import crear_fondo_pool_v3
from generator.v3.adapter.persistir_adapter import persistir_video_v3
from generator.v3.adapter.composer_adapter import componer_video_v3

from generator.v3.generator.cleanup import limpiar_temporales
from generator.v3.generator.audio.tts_edge import generar_voz_edge
from generator.v3.generator.audio.silence import generar_silencio

TEST_MAX_DURATION_SECONDS = 180  # 3 minutos
TEST_MAX_IMAGES = 2


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def cargar_bloques_texto(base_path: str, bloques: list[str]) -> list[str]:
    textos = []
    for b in bloques:
        path = os.path.join(base_path, b)
        with open(path, "r", encoding="utf-8") as f:
            textos.append(f.read().strip())
    return textos


def construir_texto_tractor(
    textos_base: list[str],
    textos_repetibles: list[str],
    target_minutes: int,
    modo_test: bool,
) -> list[str]:
    """
    Construye la secuencia final de bloques hasta alcanzar
    target_minutes (aprox), repitiendo solo los bloques permitidos.
    """
    bloques_finales = textos_base[:]

    if modo_test:
        return bloques_finales

    segundos_objetivo = target_minutes * 60
    duracion_actual = 0

    # estimación inicial (muy conservadora)
    for t in bloques_finales:
        duracion_actual += max(len(t.split()) * 0.45, 20)

    idx = 0
    while duracion_actual < segundos_objetivo:
        bloque = textos_repetibles[idx % len(textos_repetibles)]
        bloques_finales.append(bloque)
        duracion_actual += max(len(bloque.split()) * 0.45, 20)
        idx += 1

    return bloques_finales


# ---------------------------------------------------------
# Engine TRACTOR
# ---------------------------------------------------------

def generar_long_tractor(
    *,
    text_path: str, #No se ocupa, se crea para mantener firma
    resolved_config: dict,
    output_path: str,
    video_id: str,
    channel_id: int,
    modo_test: bool = False,
    force_tts: bool | None = None,
    music_path: str | None = None,
):
    print("[GENERAR LONG TRACTOR]")

    format_code = resolved_config["format"]["code"]

    # -------------------------------------------------
    # CONFIG
    # -------------------------------------------------
    content_cfg = resolved_config["content"]
    visual_cfg = resolved_config["visual"]
    audio_cfg = resolved_config["audio"]

    print("[LONG TRACTOR] Modo test:", modo_test)
    print("[LONG TRACTOR] Content CFG ", content_cfg)
    print(f"[LONG TRACTOR] VIsual CFG: {visual_cfg}")
    print(f"[LONG TRACTOR] Audio CFG: {audio_cfg}")

    if modo_test:
        target_minutes = 3
    else:
        target_minutes = resolved_config.get("target_duration_minutes", 55)



    # -------------------------------------------------
    # Cargar textos base
    # -------------------------------------------------
    print("[LONG TRACTOR] Cargando bloques de texto...")
    textos_base = cargar_bloques_texto(
        content_cfg["base_path"],
        content_cfg["blocks"],
    )
    print(f"[LONG TRACTOR] {len(textos_base)} bloques base cargados.")
    
    print("[LONG TRACTOR] Cargando bloques de texto repetibles...")
    textos_repetibles = cargar_bloques_texto(
        content_cfg["base_path"],
        content_cfg["repeatable_blocks"],
    )
    print(f"[LONG TRACTOR] {len(textos_repetibles)} bloques repetibles cargados.")


    print("[LONG TRACTOR] Construyendo texto final...")
    textos_finales = construir_texto_tractor(
        textos_base=textos_base,
        textos_repetibles=textos_repetibles,
        target_minutes=target_minutes,
        modo_test=modo_test,
    )
    print(f"[LONG TRACTOR] Texto final construido con {len(textos_finales)} bloques.")


    texto_completo = "\n\n".join(textos_finales)
    print(f"[LONG TRACTOR] Texto completo tiene {len(texto_completo.split())} palabras.")

    # -------------------------------------------------
    # TTS continuo
    # -------------------------------------------------
    voces = []
    duraciones = []

    usar_tts = bool(audio_cfg["tts"].get("enabled", True))
    if force_tts is not None:
        usar_tts = force_tts

    print("[LONG TRACTOR] Usar TTS:", usar_tts)
    if usar_tts:
        for bloque in textos_finales:
            tts_path = f"tmp/tts_{uuid.uuid4().hex}.wav"
            voz = generar_voz_edge(
                texto=bloque,
                salida_wav=tts_path
            )
            voces.append(voz)
            duraciones.append(voz.duration)

            # pausa mínima respirable
            silencio = generar_silencio(
                audio_cfg["tts"].get("pause_between_blocks", 0.4)
            )
            voces.append(silencio)
            duraciones.append(silencio.duration)

        voz_compuesta = concatenate_audioclips(voces)
        dur_total = voz_compuesta.duration

    else:
        raise RuntimeError("TRACTOR requiere TTS habilitado")

    # -------------------------------------------------
    # Fondo visual (image pool)
    # -------------------------------------------------

    image_duration = visual_cfg["image_duration_seconds"]

    if modo_test:
        image_duration = min(image_duration, TEST_MAX_DURATION_SECONDS / TEST_MAX_IMAGES)


    fondo, grad = crear_fondo_pool_v3(
        duracion_total=dur_total,
        base_path=visual_cfg["base_path"],
        image_duration_seconds=image_duration,
        transition_cfg=visual_cfg.get("transition"),
        motion_cfg=visual_cfg.get("motion"),
    )

    # -------------------------------------------------
    # Música base (loop)
    # -------------------------------------------------
    musica_clip = None
    musica_usada = None

    music_cfg = audio_cfg["music"]
    if music_cfg.get("enabled"):
        musica_clip, musica_usada = crear_audio_tractor_v3(
            duracion=dur_total,
            music_path=music_cfg["base_path"],
            track=music_cfg["track"],
            loop_cfg=music_cfg.get("loop"),
        )
        musica_clip = musica_clip.volumex(
            10 ** (music_cfg.get("volume", -26) / 20)
        )

    audio_final = CompositeAudioClip(
        [c for c in [musica_clip, voz_compuesta] if c]
    )

    if modo_test and dur_total > TEST_MAX_DURATION_SECONDS:
        voz_compuesta = voz_compuesta.subclip(0, TEST_MAX_DURATION_SECONDS)
        dur_total = voz_compuesta.duration


    # -------------------------------------------------
    # Fingerprint + deduplicación
    # -------------------------------------------------
    duracion_norm = int(round(dur_total))

    audio, musica_usada, fingerprint = resolver_audio_y_fingerprint_v3(
        tipo=format_code,
        texto=texto_completo,
        imagen_usada="POOL",
        audio_duracion=duracion_norm,
        usar_tts=True,
        audio_inicial=(audio_final, musica_usada),
    )

    licencia_path = ( 
        audio_cfg['music']['base_path'] + "/licence/licence_" + musica_usada.replace('.mp3','') + ".txt"
        if musica_usada
        else None
    )

    # -------------------------------------------------
    # Composición final
    # -------------------------------------------------
    componer_video_v3(
        fondo=fondo,
        grad=grad,
        titulo_clip=None,
        audio=audio,
        text_clips=[],
        output_path=output_path,
        visual_cfg=None,
        cta_cfg={"enabled": False},
        base_path_assest=None,
    )

    if not os.path.exists(output_path):
        raise RuntimeError("No se pudo generar el video tractor")

    # -------------------------------------------------
    # Persistencia
    # -------------------------------------------------
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo=format_code,
        output_path=output_path,
        texto=texto_completo,
        imagen_usada="POOL",
        musica_usada=musica_usada,
        fingerprint=fingerprint,
        usar_tts=True,
        modo_test=modo_test,
        licencia_path=licencia_path,
    )

    limpiar_temporales(None)

    print("[LONG TRACTOR] Video generado correctamente")
