import os
from generar_descripcion import generar_descripcion
from generar_descripcion import generar_tags_from_descripcion  


def seleccionar_archivo():
    print("\n=== Selecciona el archivo de prueba ===\n")

    print("Tipos:")
    print("1) Oración")
    print("2) Salmo")

    tipo_i = input("Selecciona tipo (1 o 2): ").strip()
    
    if tipo_i == "1":
        tipo = "oracion"
        carpeta = "textos/oraciones"   # 👈 nombre correcto
    else:
        tipo = "salmo"
        carpeta = "textos/salmos"      # 👈 nombre correcto

    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]

    print("\nArchivos disponibles:")
    for i, a in enumerate(archivos, start=1):
        print(f"{i}) {a}")

    sel = int(input("\nNúmero del archivo: ").strip())
    archivo_elegido = archivos[sel - 1]

    return tipo, os.path.join(carpeta, archivo_elegido)

def seleccionar_momento():
    """
    Tres horarios simulados, igual que tu sistema real.
    """
    print("\n=== Selecciona el MOMENTO del día ===")
    print("1) Mañana (05:00)")
    print("2) Mediodía (12:00)")
    print("3) Noche (19:00)")

    sel = input("Elige (1/2/3): ").strip()

    if sel == "1":
        return "05:00"
    if sel == "2":
        return "12:00"
    return "19:00"


def test_ia():
    print("\n========================================")
    print("      TEST GENERADOR DE DESCRIPCIÓN")
    print("========================================\n")

    tipo, archivo_texto = seleccionar_archivo()
    hora = seleccionar_momento()

    print("\nGenerando descripción...\n")

    descripcion = generar_descripcion(tipo, hora, archivo_texto)

    print("\n----------------------------------------")
    print("📌 DESCRIPCIÓN COMPLETA GENERADA POR IA")
    print("----------------------------------------\n")
    print(descripcion)
    print("\n----------------------------------------\n")

    # ===== Extraer hashtags detectados =====
    hashtags = [p for p in descripcion.split() if p.startswith("#")]

    if hashtags:
        print("🔖 HASHTAGS DETECTADOS EN EL TEXTO:")
        print(" ".join(hashtags))
    else:
        print("⚠ La IA NO generó hashtags (se usó fallback).")

    print("\n----------------------------------------")

    # ===== Simular los tags que se enviarán a YouTube =====
    tags_para_youtube = generar_tags_from_descripcion(descripcion)

    print("\n🎯 TAGS QUE SE ENVIARÍAN A YOUTUBE:")
    print(tags_para_youtube)

    print("\n========================================\n")


if __name__ == "__main__":
    while True:
        test_ia()
        again = input("¿Quieres probar otra vez? (s/n): ").strip().lower()
        if again != "s":
            break

    print("\nTest finalizado.\n")
