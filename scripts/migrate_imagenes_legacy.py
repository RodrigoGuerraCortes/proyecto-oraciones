import os
from db.connection import get_connection

IMAGENES_DIR = "imagenes"
EXT_VALIDAS = (".png", ".jpg", ".jpeg", ".webp")


# --------------------------------------------------
# 1. Indexar filesystem: imagen -> categoria
# --------------------------------------------------
index = {}  # "30.png" -> "jesus"

for categoria in os.listdir(IMAGENES_DIR):
    cat_path = os.path.join(IMAGENES_DIR, categoria)
    if not os.path.isdir(cat_path):
        continue

    for f in os.listdir(cat_path):
        if f.lower().endswith(EXT_VALIDAS):
            index[f] = categoria

print(f"[INFO] Indexadas {len(index)} imágenes desde filesystem")


# --------------------------------------------------
# 2. Leer registros legacy desde BD
# --------------------------------------------------
query_select = """
    SELECT id, imagen
    FROM videos
    WHERE imagen IS NOT NULL
      AND imagen NOT LIKE '%/%'
"""

query_update = """
    UPDATE videos
    SET imagen = %(imagen)s
    WHERE id = %(id)s
"""

migrados = 0
no_encontrados = 0

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(query_select)
        rows = cur.fetchall()

        print(f"[INFO] Encontrados {len(rows)} registros legacy")

        for row in rows:
            video_id = row["id"]
            img = row["imagen"]

            print(f"[DEBUG] id={video_id}, img={repr(img)}")

            categoria = index.get(img)
            if not categoria:
                print(f"[WARN] Imagen no encontrada en filesystem: {img}")
                continue

            nueva = f"{categoria}/{img}"

            cur.execute(query_update, {
                "imagen": nueva,
                "id": video_id
            })

            migrados += 1

    conn.commit()

print("===================================")
print(f"Migrados correctamente: {migrados}")
print(f"No encontrados: {no_encontrados}")
