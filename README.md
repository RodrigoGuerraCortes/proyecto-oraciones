python3 generar_video.py 1 oracion
python3 generar_video.py 1 salmo



python3 generar_video.py solo textos/oraciones/oracion_de_la_mañana.txt


python3 generar_video.py solo textos/salmos/salmo_23_el_senor_es_mi_pastor.txt



python3 generar_video.py solo textos/salmos/salmo_23_el_senor_es_mi_pastor.txt --imagen=22.png --musica=5.mp3



python3 generar_video.py 1 salmo test



python3 subir_videos_diarios.py



planificar.py -> crea los videos con el sistema OSO 
subir_video_xxxxx -> sube el video a x plataforma y actualiza el historial 
gestor_publicacion -> revisa si ya los videos fueron publicados y mueve de pendientes a publicados.




#Para tik tok

🟢 Paso 2 — Bootstrap OAuth (una sola vez)
python3 generar_token_tiktok.py --oauth

python3 subir_video_tiktok.py
