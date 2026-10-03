"""Tests del buscador de modelos RNA disponibles."""

import json
from pathlib import Path

import pytest

from logica import buscador_modelos


def _crear_modelo_valido(carpeta, nv=2, tipo='RNA'):
    """Crea una carpeta con los 4 archivos de un modelo RNA válido."""
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / 'config.json').write_text(
        json.dumps({'tipo': tipo, 'version': 1, 'nv': nv,
                    'lim_inf': [-1] * nv, 'lim_sup': [1] * nv,
                    'columnas_x': [f'x{i+1}' for i in range(nv)]}),
        encoding='utf-8',
    )
    (carpeta / 'modelo.keras').write_bytes(b'fake')
    (carpeta / 'scaler_x.save').write_bytes(b'fake')
    (carpeta / 'scaler_y.save').write_bytes(b'fake')


# ------------------------------------------------------------------

def test_sin_modelos(tmp_path):
    assert buscador_modelos.buscar_modelos_disponibles(tmp_path) == []


def test_un_modelo_valido(tmp_path):
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'rna1', nv=3)
    modelos = buscador_modelos.buscar_modelos_disponibles(tmp_path)
    assert len(modelos) == 1
    assert modelos[0]['nombre'] == 'rna1'
    assert modelos[0]['nv'] == 3
    assert 'display' in modelos[0]


def test_tipo_distinto_se_ignora(tmp_path):
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'otro', tipo='XYZ')
    assert buscador_modelos.buscar_modelos_disponibles(tmp_path) == []


def test_modelo_incompleto_se_ignora(tmp_path):
    carpeta = tmp_path / 'exportaciones' / 'incompleto'
    carpeta.mkdir(parents=True)
    (carpeta / 'config.json').write_text(
        json.dumps({'tipo': 'RNA', 'nv': 2}), encoding='utf-8',
    )
    # Faltan modelo.keras, scaler_x.save, scaler_y.save
    assert buscador_modelos.buscar_modelos_disponibles(tmp_path) == []


def test_orden_por_mtime_descendente(tmp_path):
    import time
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'viejo')
    time.sleep(0.05)
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'nuevo')

    modelos = buscador_modelos.buscar_modelos_disponibles(tmp_path)
    assert len(modelos) == 2
    assert modelos[0]['nombre'] == 'nuevo'
    assert modelos[1]['nombre'] == 'viejo'


def test_carpetas_ignoradas(tmp_path):
    _crear_modelo_valido(tmp_path / 'resultados_pso' / 'ignorado')
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'valido')

    modelos = buscador_modelos.buscar_modelos_disponibles(tmp_path)
    assert len(modelos) == 1
    assert modelos[0]['nombre'] == 'valido'


def test_resolver_ruta_por_display(tmp_path):
    _crear_modelo_valido(tmp_path / 'exportaciones' / 'rna1')
    modelos = buscador_modelos.buscar_modelos_disponibles(tmp_path)
    ruta = buscador_modelos.resolver_ruta(modelos[0]['display'], modelos)
    assert Path(ruta).name == 'rna1'


def test_resolver_ruta_manual(tmp_path):
    modelos = []
    ruta = buscador_modelos.resolver_ruta('C:/ruta/manual', modelos)
    assert ruta == 'C:/ruta/manual'


def test_resolver_ruta_vacia():
    assert buscador_modelos.resolver_ruta('', []) == ''