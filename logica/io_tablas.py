"""Utilidades para leer y escribir tablas en varios formatos.

Detecta el formato por extensión y delega a pandas:

- ``.xlsx`` / ``.xls`` → Excel vía ``openpyxl``.
- ``.csv``             → texto plano (compatibilidad hacia atrás).

Este módulo no depende de PySimpleGUI ni de ningún otro módulo del
proyecto, para poder usarse desde cualquier capa.
"""

import logging
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)

EXT_EXCEL = {'.xlsx', '.xls'}


# ----------------------------------------------------------------------
# Filtros para diálogos
# ----------------------------------------------------------------------

def filtros_lectura():
    """file_types para leer: Excel primero, CSV como opción secundaria."""
    return (("Excel", "*.xlsx"), ("CSV", "*.csv"))


def filtros_escritura():
    """file_types para escribir: solo Excel."""
    return (("Excel", "*.xlsx"),)


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

def leer_tabla(archivo, dtype=None, hoja=0):
    """Lee un archivo tabular detectando formato por extensión.

    - ``.xlsx`` / ``.xls`` → ``pd.read_excel``
    - ``.csv``             → ``pd.read_csv`` (utf-8)

    Devuelve un ``DataFrame``.
    """
    ruta = Path(archivo)
    ext = ruta.suffix.lower()
    if ext in EXT_EXCEL:
        return pd.read_excel(ruta, dtype=dtype, sheet_name=hoja)
    return pd.read_csv(ruta, dtype=dtype, encoding='utf-8')


# ----------------------------------------------------------------------
# Escritura
# ----------------------------------------------------------------------

def escribir_tabla(df, destino, hoja='Sheet1'):
    """Escribe un DataFrame al formato deducido por la extensión.

    - ``.xlsx`` / ``.xls`` → ``df.to_excel`` con nombre de hoja
    - cualquier otra       → ``df.to_csv`` (utf-8)

    Devuelve la ruta efectiva.
    """
    ruta = Path(destino)
    ext = ruta.suffix.lower()
    if ext in EXT_EXCEL:
        df.to_excel(ruta, index=False, sheet_name=hoja)
    else:
        df.to_csv(ruta, index=False, encoding='utf-8')
    return ruta