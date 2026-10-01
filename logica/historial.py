"""Persistencia del historial de ejecuciones del PSO.

Cada ejecución exitosa del PSO se registra como un diccionario en
``resultados_pso/historial_ejecuciones.json``. El historial tiene un tope
de 200 entradas: al superarlo, se descartan las más antiguas.

Funciones puras, sin dependencia de PySimpleGUI. Se puede testear en
aislamiento.
"""

import json
import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)

ARCHIVO = Path('resultados_pso') / 'historial_ejecuciones.json'
MAX_ENTRADAS = 200


# ----------------------------------------------------------------------
# Carga / guardado
# ----------------------------------------------------------------------

def cargar_historial():
    """Devuelve la lista de entradas.

    Si el archivo no existe, devuelve ``[]``.
    Si está corrupto, lo ignora, registra un warning y devuelve ``[]``.
    """
    if not ARCHIVO.exists():
        return []
    try:
        with open(ARCHIVO, encoding='utf-8') as f:
            datos = json.load(f)
        if not isinstance(datos, list):
            logger.warning("Historial no es una lista. Ignorando contenido.")
            return []
        return datos
    except Exception as exc:
        logger.warning(f"Historial corrupto ({exc}). Empezando de cero.")
        return []


def guardar_historial(entradas):
    """Escribe la lista completa al archivo, creando la carpeta si falta."""
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(ARCHIVO, 'w', encoding='utf-8') as f:
            json.dump(entradas, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.error(f"No se pudo guardar el historial: {exc}")


# ----------------------------------------------------------------------
# Operaciones
# ----------------------------------------------------------------------

def agregar_entrada(entrada):
    """Añade una entrada. Asigna ``id`` y ``timestamp`` si faltan.

    Aplica el tope de ``MAX_ENTRADAS`` descartando las más antiguas.
    Reasigna los ``id`` secuencialmente tras el truncado para que sigan
    siendo coherentes (1, 2, 3, ...).
    """
    historial = cargar_historial()
    entrada = dict(entrada)
    entrada.setdefault(
        'timestamp', datetime.now().isoformat(timespec='seconds')
    )
    historial.append(entrada)

    if len(historial) > MAX_ENTRADAS:
        historial = historial[-MAX_ENTRADAS:]

    for i, e in enumerate(historial, start=1):
        e['id'] = i

    guardar_historial(historial)
    return historial[-1]


def limpiar_historial():
    """Vacía el historial."""
    guardar_historial([])