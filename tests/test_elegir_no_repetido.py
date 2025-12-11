import os
import shutil
import pytest
from datetime import datetime, timedelta

from logic.text_seleccion import elegir_no_repetido


# ==========================================================
# FIXTURE: preparar carpeta temporal con 5 textos
# ==========================================================
@pytest.fixture
def carpeta_oraciones(tmp_path):
    """
    Crea una carpeta temporal:
        tmp/test_oraciones
    con 5 archivos .txt de prueba.
    Devuelve la ruta como string.
    """
    carpeta = tmp_path / "test_oraciones"
    carpeta.mkdir()

    for i in range(1, 6):
        (carpeta / f"oracion_{i}.txt").write_text(f"Contenido {i}")

    return str(carpeta)


# ==========================================================
# FIXTURE: historial base
# ==========================================================
@pytest.fixture
def historial_base():
    """Historial válido pero vacío."""
    return {
        "pendientes": [],
        "publicados": [],
        "textos_usados": {}
    }


# ==========================================================
# TEST 1: No se debe elegir un texto que está en pendientes
# ==========================================================
def test_no_repite_pendientes(carpeta_oraciones, historial_base):

    historial_base["pendientes"] = [
        {"archivo": "videos/oraciones/oracion_3.mp4"}
    ]
    historial_base["textos_usados"][carpeta_oraciones] = []

    elegido = elegir_no_repetido(carpeta_oraciones, historial_base)

    assert elegido != "oracion_3.txt", \
        f"Eligió un texto que está pendiente: {elegido}"


# ==========================================================
# TEST 2: No se debe elegir un texto que está publicado
# ==========================================================
def test_no_repite_publicados(carpeta_oraciones, historial_base):

    historial_base["publicados"] = [
        {"archivo": "videos/oraciones/oracion_2.mp4"}
    ]
    historial_base["textos_usados"][carpeta_oraciones] = []

    elegido = elegir_no_repetido(carpeta_oraciones, historial_base)

    assert elegido != "oracion_2.txt", \
        f"Eligió un texto que ya está publicado: {elegido}"


# ==========================================================
# TEST 3: No repetir textos usados en los últimos 7 días
# ==========================================================
def test_no_repite_en_7_dias(carpeta_oraciones, historial_base):

    hace_2_dias = (datetime.now() - timedelta(days=2)).isoformat()

    historial_base["textos_usados"][carpeta_oraciones] = [
        {"nombre": "oracion_4", "fecha": hace_2_dias}
    ]

    elegido = elegir_no_repetido(carpeta_oraciones, historial_base)

    assert elegido != "oracion_4.txt", \
        f"Eligió un texto usado hace 2 días: {elegido}"


# ==========================================================
# TEST 4: RESET si todos los textos están ocupados < 7 días
# ==========================================================
def test_reset_correcto(carpeta_oraciones, historial_base):

    hace_8_dias = (datetime.now() - timedelta(days=8)).isoformat()

    # Simula que todos fueron usados pero hace más de 7 días (permitiendo reset)
    historial_base["textos_usados"][carpeta_oraciones] = [
        {"nombre": f"oracion_{i}", "fecha": hace_8_dias}
        for i in range(1, 6)
    ]

    elegido = elegir_no_repetido(carpeta_oraciones, historial_base)

    assert elegido in [f"oracion_{i}.txt" for i in range(1, 6)], \
        f"El reset no funcionó: eligió {elegido}"


# ==========================================================
# TEST 5: Cuando se agoten los disponibles → se reinicia correctamente
# ==========================================================
def test_reset_por_agotamiento(carpeta_oraciones, historial_base):
    """
    Caso extremo:
    - Todos los textos fueron usados hace 1 día → NO disponibles.
    - Debe resetear y elegir cualquiera.
    """
    ayer = (datetime.now() - timedelta(days=1)).isoformat()

    historial_base["textos_usados"][carpeta_oraciones] = [
        {"nombre": f"oracion_{i}", "fecha": ayer}
        for i in range(1, 6)
    ]

    elegido = elegir_no_repetido(carpeta_oraciones, historial_base)

    assert elegido in [f"oracion_{i}.txt" for i in range(1, 6)], \
        f"Reset por agotamiento falló: {elegido}"
