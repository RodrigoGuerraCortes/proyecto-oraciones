from db.connection import get_connection  # o como tengas la DB hoy


def list_channels() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, code, nombre, activo, created_at
        FROM channels
        ORDER BY id
    """)

    rows = cur.fetchall()

    return [
        {
            "id": r['id'],
            "code": r['code'],
            "name": r['nombre'],
            "active": r['activo'],
            "created_at": r['created_at'],
        }
        for r in rows
    ]
