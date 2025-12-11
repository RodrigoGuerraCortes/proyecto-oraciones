#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from datetime import datetime, timedelta

from historial import cargar_historial, guardar_historial

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERADOR = os.path.join(BASE_DIR, "generar_video_v2.py")

# Regla A → OSO POR DÍA
SLOTS_DEL_DIA = {
    "11:00": "oracion",   # O
    "15:30": "salmo",     # S
    "23:10": "oracion"    # O
}
HORARIOS = list(SLOTS_DEL_DIA.keys())


# ==========================================================
# Helpers
# ==========================================================
def parsear_publicar_en(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        # Caso legacy HH:MM
        try:
            hh, mm = map(int, valor.split(":"))
            hoy = datetime.now().date()
            return datetime(hoy.year, hoy.month, hoy.day, hh, mm)
        except:
            return None


def mapear_slots_por_fecha(hist):
    por_fecha = {}
    for grupo in ("pendientes", "publicados"):
        for item in hist.get(grupo, []):
            dt = parsear_publicar_en(item.get("publicar_en"))
            if not dt:
                continue
            por_fecha.setdefault(dt.date(), []).append(item)
    return por_fecha


def slots_faltantes_en_dia(fecha, por_fecha):
    """
    Devuelve lista de (hora, tipo) para los slots OSO faltantes.
    Ej: [("23:10", "oracion")]
    """
    usados = set()

    for item in por_fecha.get(fecha, []):
        dt = parsear_publicar_en(item.get("publicar_en"))
        if not dt:
            continue
        hora = dt.strftime("%H:%M")
        usados.add(hora)

    faltantes = []
    for hora, tipo in SLOTS_DEL_DIA.items():
        if hora not in usados:
            faltantes.append((hora, tipo))

    return faltantes


# ==========================================================
# Ejecutores
# ==========================================================
def generar_un_video(tipo, modo_test=False):
    cmd = [PYTHON, GENERADOR, "1", tipo]
    if modo_test:
        cmd.append("test")
    print(f"[PLANIFICAR] Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd)


def generar_por_lista(lista_slots, modo_test=False):
    """
    lista_slots = [(hora, tipo), ...]
    """
    for hora, tipo in lista_slots:
        print(f"[PLANIFICAR] Generando '{tipo}' para slot {hora}")
        generar_un_video(tipo, modo_test)


# ==========================================================
# Comportamiento por defecto: completar HOY + 1 día más
# ==========================================================
def completar_hoy_y_dos_dias(modo_test=False):
    hist = cargar_historial()
    por_fecha = mapear_slots_por_fecha(hist)

    hoy = datetime.now().date()
    manana = hoy + timedelta(days=1)
    pasado = hoy + timedelta(days=2)

    faltan_hoy = slots_faltantes_en_dia(hoy, por_fecha)
    faltan_manana = slots_faltantes_en_dia(manana, por_fecha)
    faltan_pasado = slots_faltantes_en_dia(pasado, por_fecha)

    print("========================================")
    print("[PLANIFICAR] DEFAULT (Regla A: OSO por día – 3 días)")
    print("========================================")
    print(f"Hoy            {hoy}: faltan {faltan_hoy}")
    print(f"Mañana         {manana}: faltan {faltan_manana}")
    print(f"Pasado mañana  {pasado}: faltan {faltan_pasado}")

    total_slots = faltan_hoy + faltan_manana + faltan_pasado
    print(f"[PLANIFICAR] Total a generar: {len(total_slots)}")

    generar_por_lista(total_slots, modo_test)

# ==========================================================
# --dias = generar N días completos OSO (sin tocar hoy)
# ==========================================================
def planificar_dias(n, modo_test=False):
    hist = cargar_historial()
    por_fecha = mapear_slots_por_fecha(hist)

    hoy = datetime.now().date()
    total_slots = []

    print("========================================")
    print(f"[PLANIFICAR] Generar {n} días completos desde mañana")
    print("========================================")

    for offset in range(1, n + 1):
        dia = hoy + timedelta(days=offset)
        faltantes = slots_faltantes_en_dia(dia, por_fecha)
        print(f"[PLANIFICAR] Día {dia}: faltan {faltantes}")
        total_slots += faltantes

    print(f"[PLANIFICAR] Total a generar: {len(total_slots)}")

    generar_por_lista(total_slots, modo_test)


# ==========================================================
# --solo-hoy
# ==========================================================
def solo_hoy(modo_test=False):
    hist = cargar_historial()
    por_fecha = mapear_slots_por_fecha(hist)

    hoy = datetime.now().date()
    faltantes = slots_faltantes_en_dia(hoy, por_fecha)

    print(f"[PLANIFICAR] SOLO HOY → faltan: {faltantes}")
    generar_por_lista(faltantes, modo_test)


# ==========================================================
# --reset-manana
# ==========================================================
def reset_manana(modo_test=False):
    hoy = datetime.now().date()
    manana = hoy + timedelta(days=1)

    hist = cargar_historial()
    nuevos_pendientes = []

    for p in hist.get("pendientes", []):
        dt = parsear_publicar_en(p.get("publicar_en"))
        if dt and dt.date() == manana:
            print(f"[RESET] Eliminando pendiente: {p['archivo']}")
            continue
        nuevos_pendientes.append(p)

    hist["pendientes"] = nuevos_pendientes
    guardar_historial(hist)

    print("[RESET] Regenerando OSO completo para mañana")
    lista = [(hora, tipo) for hora, tipo in SLOTS_DEL_DIA.items()]
    generar_por_lista(lista, modo_test)


# ==========================================================
# ENTRY POINT
# ==========================================================
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--test", action="store_true")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--solo-hoy", action="store_true")
    group.add_argument("--completar-hoy", action="store_true")
    group.add_argument("--dias", type=int)
    group.add_argument("--reset-manana", action="store_true")

    args = parser.parse_args()
    modo_test = args.test

    if args.solo_hoy or args.completar_hoy:
        solo_hoy(modo_test)
    elif args.dias is not None:
        planificar_dias(args.dias, modo_test)
    elif args.reset_manana:
        reset_manana(modo_test)
    else:
        completar_hoy_y_dos_dias(modo_test)


if __name__ == "__main__":
    main()
