# Proyecto Oraciones y Salmos Automáticos  
Automatización completa para generar videos católicos (Oraciones y Salmos) en formato vertical 1080x1920 para YouTube, TikTok y Facebook.  
Incluye manejo de imágenes, música, generación automática diaria, historial inteligente y generación manual con imagen/música fija.

---

## 📌 Características principales

### ✔ Generación automática de videos diarios
El script `generar_videos_diarios.py` crea:
- Oración de la mañana → 05:00  
- Salmo del día → 12:00  
- Oración de la noche → 19:00

### ✔ Generación manual de un video con parámetros
Nueva característica:

python3 generar_video.py solo ruta/salmo_23.txt
--imagen=28.png
--musica=6.mp3



Permite:
- Usar **una imagen exacta**
- Usar **una música específica**
- No repetir assets automáticamente

### ✔ Historial inteligente unificado
El archivo `historial.json` registra:

- `pendientes`: videos generados pero no publicados  
- `publicados`: videos subidos a YouTube  
- `imagenes`: imágenes usadas recientemente  
- `musicas`: músicas usadas recientemente  
- `oraciones` y `salmos`: textos usados para evitar repetición

### ✔ Registrar uso de música e imágenes automáticamente
Desde cualquier punto del programa:

```python
registrar_uso("imagenes", "20.png")
registrar_uso("musicas", "8.mp3")

Esto actualiza el historial sin borrar otro contenido.

✔ Sistema anti-repetición de contenido

elegir_no_repetido() garantiza que:

No se repita un salmo/oración dentro de X días

Si se agotan, se reinicia la lista

✔ Modo test (10 segundos)

python3 generar_video.py 1 salmo test


proyecto-oraciones/
│
├── generar_video.py
├── generar_videos_diarios.py
├── historial.py
├── historial.json
│
├── imagenes/
│   ├── vignette.png
│   ├── 1.png
│   └── ...
│
├── musica/
│   ├── 1.mp3
│   ├── 2.mp3
│   └── ...
│
├── textos/
│   ├── oraciones/
│   └── salmos/
│
└── videos/
    ├── oraciones/
    └── salmos/
