from generator.generar_oracion import generar_oracion
import uuid

video_id = uuid.uuid4()

generar_oracion(
    video_id=video_id,
    path_in="textos/manual/oracion_ano_nuevo_2026.txt",
    path_out="videos/oraciones/ano_nuevo_2026.mp4",
    modo_test=False,
    force_tts=True
)