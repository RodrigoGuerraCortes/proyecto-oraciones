# generator/pipeline.py
import uuid
from generator.generar_oracion import generar_oracion
from generator.generar_salmo import generar_salmo
from generator.generar_oracion_long import generar_oracion_long


def generar_videos(tipo: str, cantidad: int, modo_test: bool = False, force_one_tts: bool = False):
    """
    Genera N videos del tipo indicado usando el pipeline.
    - tipo: 'oracion' | 'salmo' | 'long'
    """
    from generator.content.selector import elegir_texto_para

    assert tipo in ("oracion", "salmo", "long"), f"Tipo inválido: {tipo}"

    print(f"[PIPELINE] Generando {cantidad} videos tipo={tipo}")

    tts_forzado_pendiente = force_one_tts

    for i in range(cantidad):

        force_tts = None
        if tts_forzado_pendiente:
            force_tts = True
            tts_forzado_pendiente = False

        # Reutilizamos selector existente
        path_txt, base = elegir_texto_para("oracion" if tipo == "long" else tipo)

        video_id = uuid.uuid4()
        video_id_short = str(video_id).split("-")[0]

        if tipo == "oracion":
            carpeta = "videos/test/oraciones" if modo_test else "videos/oraciones"

        elif tipo == "long":
            carpeta = "videos/test/oraciones_long" if modo_test else "videos/oraciones_long"

        else:
            carpeta = "videos/test/salmos" if modo_test else "videos/salmos"

        salida = f"{carpeta}/{video_id_short}__{base}.mp4"

        if tipo == "oracion":
            generar_oracion(
                video_id=video_id,
                path_in=path_txt,
                path_out=salida,
                modo_test=modo_test,
                force_tts=force_tts
            )

        elif tipo == "long":
            generar_oracion_long(
                video_id=video_id,
                path_in=path_txt,
                path_out=salida,
                modo_test=modo_test
            )

        else:
            generar_salmo(
                video_id=video_id,
                path_in=path_txt,
                path_out=salida,
                modo_test=modo_test
            )

        print(f"[PIPELINE] OK {i+1}/{cantidad} → {salida}")
