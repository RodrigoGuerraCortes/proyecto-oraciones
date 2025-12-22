import os
from collections import Counter
from db.connection import get_connection

BASE_DIR = "videos"

def listar_videos_disco():
    files = []
    for root, _, filenames in os.walk(BASE_DIR):
        for f in filenames:
            if f.endswith(".mp4"):
                files.append(os.path.join(root, f))
    return set(files)

def listar_videos_bd():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, archivo
                FROM videos
            """)
            rows = cur.fetchall()
    return rows

def main():
    disco = listar_videos_disco()
    rows = listar_videos_bd()

    bd_archivos = [r["archivo"] for r in rows]

    set_bd = set(bd_archivos)

    print("========== CHECK INVENTARIO ==========")

    # 1️⃣ En BD pero no en disco
    faltantes = set_bd - disco
    print(f"\n❌ En BD pero NO en disco: {len(faltantes)}")
    for f in list(faltantes)[:10]:
        print("  -", f)

    # 2️⃣ En disco pero no en BD
    huérfanos = disco - set_bd
    print(f"\n⚠️ En disco pero NO en BD: {len(huérfanos)}")
    for f in list(huérfanos)[:10]:
        print("  -", f)

    # 3️⃣ Duplicados en BD
    counter = Counter(bd_archivos)
    duplicados = {k: v for k, v in counter.items() if v > 1}

    print(f"\n🔁 Duplicados en BD: {len(duplicados)}")
    for k, v in list(duplicados.items())[:10]:
        print(f"  - {k} → {v} veces")

    print("\n========== FIN CHECK ==========")

if __name__ == "__main__":
    main()
