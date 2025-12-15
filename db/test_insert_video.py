import uuid
from datetime import datetime
from db.repositories.video_repo import insert_video, get_video_by_id

video_id = uuid.uuid4()

insert_video({
    "id": video_id,
    "channel_id": 3,  # asegúrate de que existe
    "archivo": "videos/oraciones/test_video.mp4",
    "tipo": "oracion",
    "musica": "5.mp3",
    "licencia": None,
    "imagen": "13.png",
    "texto_base": "oracion_test",
    "fecha_generado": datetime.now(),
})

video = get_video_by_id(video_id)
print(video)
