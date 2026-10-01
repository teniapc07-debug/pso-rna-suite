"""Tests del módulo de historial de ejecuciones."""

import json
from pathlib import Path

import pytest

from logica import historial


@pytest.fixture
def archivo_temporal(tmp_path, monkeypatch):
    """Redirige el archivo de historial a una carpeta temporal."""
    archivo = tmp_path / 'historial_ejecuciones.json'
    monkeypatch.setattr(historial, 'ARCHIVO', archivo)
    return archivo


def test_cargar_historial_vacio(archivo_temporal):
    assert historial.cargar_historial() == []


def test_agregar_entrada_persiste(archivo_temporal):
    entrada = {'origen': 'prueba', 'np': 10, 'mejor_valor': 0.5}
    resultado = historial.agregar_entrada(entrada)

    assert resultado['id'] == 1
    assert 'timestamp' in resultado
    assert archivo_temporal.exists()

    contenido = json.loads(archivo_temporal.read_text(encoding='utf-8'))
    assert len(contenido) == 1
    assert contenido[0]['origen'] == 'prueba'


def test_cap_200(archivo_temporal):
    for i in range(205):
        historial.agregar_entrada({'origen': f'run{i}', 'mejor_valor': i})

    contenido = historial.cargar_historial()
    assert len(contenido) == 200
    # Las primeras 5 fueron descartadas: la primera entrada actual es run5
    assert contenido[0]['origen'] == 'run5'
    # Los ids se reasignan secuencialmente
    assert contenido[0]['id'] == 1
    assert contenido[-1]['id'] == 200


def test_archivo_corrupto_se_ignora(archivo_temporal):
    archivo_temporal.parent.mkdir(parents=True, exist_ok=True)
    archivo_temporal.write_text('{ esto no es JSON }', encoding='utf-8')

    assert historial.cargar_historial() == []

    # Al agregar, debe partir de cero y sobreescribir el archivo corrupto
    historial.agregar_entrada({'origen': 'nuevo'})
    contenido = historial.cargar_historial()
    assert len(contenido) == 1
    assert contenido[0]['origen'] == 'nuevo'


def test_limpiar_historial(archivo_temporal):
    historial.agregar_entrada({'origen': 'algo'})
    assert len(historial.cargar_historial()) == 1

    historial.limpiar_historial()
    assert historial.cargar_historial() == []


def test_timestamp_por_defecto(archivo_temporal):
    resultado = historial.agregar_entrada({'origen': 'x'})
    assert 'timestamp' in resultado
    # Formato ISO con separador T
    assert 'T' in resultado['timestamp']