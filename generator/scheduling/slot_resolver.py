# generator/scheduling/slot_resolver.py
from datetime import datetime, timedelta

from historial import cargar_historial

HORARIOS_TIPO = [
    ("11:00", "oracion"),
    ("15:30", "salmo"),
    ("23:10", "oracion"),
]


def programar_publicacion_exacta(tipo: str) -> str:
    """
    Usa historial.json (pendientes+publicados) para encontrar el próximo slot libre.
    Retorna ISO string con -03:00 (como tu original).
    """
    assert tipo in ["oracion", "salmo"], f"Tipo inválido: {tipo}"

    hist = cargar_historial()
    ocupados = set()  # (date, "HH:MM")

    for lista in ("publicados", "pendientes"):
        for item in hist.get(lista, []):
            ts = item.get("publicar_en")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                continue

            ocupados.add((dt.date(), dt.strftime("%H:%M")))

    ahora = datetime.now()
    dia = ahora.date()

    for _ in range(365):
        for hora_str, tipo_slot in HORARIOS_TIPO:
            if tipo_slot != tipo:
                continue

            hh, mm = map(int, hora_str.split(":"))
            dt_slot = datetime(dia.year, dia.month, dia.day, hh, mm)

            if dt_slot <= ahora:
                continue
            if (dia, hora_str) in ocupados:
                continue

            return dt_slot.strftime("%Y-%m-%dT%H:%M:%S-03:00")

        dia = dia + timedelta(days=1)

    dt_fallback = ahora + timedelta(hours=1)
    return dt_fallback.strftime("%Y-%m-%dT%H:%M:%S-03:00")
