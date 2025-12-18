# generator/pipeline.py
import uuid
from generator.generar_oracion import generar_oracion
from generator.generar_salmo import generar_salmo

def generar_videos(tipo: str, cantidad: int, modo_test: bool = False):
    """
    Genera N videos del tipo indicado usando el pipeline.
    - tipo: 'oracion' | 'salmo'
    - cantidad: int
    """
    from generator.content.selector import elegir_texto_para

    assert tipo in ("oracion", "salmo"), f"Tipo inválido: {tipo}"

    print(f"[PIPELINE] Generando {cantidad} videos tipo={tipo}")

    for i in range(cantidad):
        path_txt, base = elegir_texto_para(tipo)

        video_id = uuid.uuid4()
        video_id_short = str(video_id).split("-")[0]

        if tipo == "oracion":
            carpeta = "videos/test/oraciones" if modo_test else "videos/oraciones"
        else:
            carpeta = "videos/test/salmos" if modo_test else "videos/salmos"

        salida = f"{carpeta}/{video_id_short}__{base}.mp4"

        if tipo == "oracion":
            generar_oracion(
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
