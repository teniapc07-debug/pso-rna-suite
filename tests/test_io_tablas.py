"""Tests del módulo de lectura/escritura de tablas."""

import pandas as pd
import pytest

from logica import io_tablas


# ----------------------------------------------------------------------
# Escritura
# ----------------------------------------------------------------------

def test_escribir_xlsx(tmp_path):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    destino = tmp_path / 'datos.xlsx'
    ruta = io_tablas.escribir_tabla(df, destino, hoja='MiHoja')
    assert ruta.exists()
    assert ruta.suffix == '.xlsx'


def test_escribir_csv(tmp_path):
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    destino = tmp_path / 'datos.csv'
    ruta = io_tablas.escribir_tabla(df, destino)
    assert ruta.exists()
    assert ruta.suffix == '.csv'


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

def test_leer_xlsx(tmp_path):
    df = pd.DataFrame({'parametro': ['NP', 'NI'], 'valor': ['30', '50']})
    destino = tmp_path / 'params.xlsx'
    io_tablas.escribir_tabla(df, destino, hoja='Parametros')

    leido = io_tablas.leer_tabla(destino, dtype=str)
    assert list(leido.columns) == ['parametro', 'valor']
    assert leido.shape == (2, 2)
    assert leido.iloc[0]['parametro'] == 'NP'


def test_leer_csv(tmp_path):
    archivo = tmp_path / 'params.csv'
    archivo.write_text('parametro,valor\nNP,30\nNI,50\n', encoding='utf-8')

    leido = io_tablas.leer_tabla(archivo, dtype=str)
    assert list(leido.columns) == ['parametro', 'valor']
    assert leido.shape == (2, 2)
    assert leido.iloc[0]['parametro'] == 'NP'


def test_leer_xlsx_hoja_especifica(tmp_path):
    destino = tmp_path / 'multi.xlsx'
    with pd.ExcelWriter(destino) as writer:
        pd.DataFrame({'a': [1]}).to_excel(writer, sheet_name='Uno', index=False)
        pd.DataFrame({'b': [2]}).to_excel(writer, sheet_name='Dos', index=False)

    df = io_tablas.leer_tabla(destino, hoja='Dos')
    assert list(df.columns) == ['b']


# ----------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------

def test_filtros_lectura():
    f = io_tablas.filtros_lectura()
    assert any('xlsx' in pat for _, pat in f)
    assert any('csv' in pat for _, pat in f)


def test_filtros_escritura():
    f = io_tablas.filtros_escritura()
    assert len(f) == 1
    assert 'xlsx' in f[0][1]