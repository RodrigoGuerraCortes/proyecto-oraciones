import os
import json
import shutil
from generar_video import crear_video_oracion, crear_video_salmo, cargar_historial_extendido, guardar_historial_extendido, elegir_no_repetido_media

# ------------------------------------------
# CONFIGURACIÓN DE TEST
# ------------------------------------------
TEST_HISTORIAL = "historial_test.json"
TEST_OUTPUT = "test_output"

# Copiar historial real sin tocarlo
if not os.path.exists(TEST_HISTORIAL):
    shutil.copy("historial.json", TEST_HISTORIAL)

# Crear carpeta temporal
os.makedirs(TEST_OUTPUT, exist_ok=True)

# ------------------------------------------
# Cargar historial de test
# ------------------------------------------
with open(TEST_HISTORIAL, "r") as f:
    hist = json.load(f)

# Asegurar claves extendidas
hist.setdefault("imagenes", [])
hist.setdefault("musicas", [])
hist.setdefault("oraciones", [])
hist.setdefault("salmos", [])

print("\n============================")
print("  INICIANDO TEST DE GENERACIÓN")
print("============================")

# ------------------------------------------
# 1) Probar selección de imágenes
# ------------------------------------------
imagenes = os.listdir("imagenes")
print("\n📌 TEST: Selección de imágenes (5 rondas)")
for i in range(5):
    elegido = elegir_no_repetido_media(imagenes, hist["imagenes"], dias_no_repetir=1)
    print(f"  Imagen elegida #{i+1}: {elegido}")

# ------------------------------------------
# 2) Probar selección de música
# ------------------------------------------
musicas = os.listdir("musica")
print("\n📌 TEST: Selección de música (5 rondas)")
for i in range(5):
    elegido = elegir_no_repetido_media(musicas, hist["musicas"], dias_no_repetir=1)
    print(f"  Música elegida #{i+1}: {elegido}")

# ------------------------------------------
# 3) Guardar historial (solo test)
# ------------------------------------------
guardar_historial_extendido(hist)

print("\n📌 TEST COMPLETADO")
print("Historial actualizado (solo test): historial_test.json")
print("\nNO se tocó historial.json real.\n")
