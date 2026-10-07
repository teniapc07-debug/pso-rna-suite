"""Rutas centralizadas del proyecto.

En desarrollo, los archivos se escriben en el cwd (junto al proyecto).
En el ejecutable empaquetado, se escriben en la carpeta del usuario.
"""

import sys
from pathlib import Path


def _es_ejecutable():
    """True si estamos corriendo desde un .exe de PyInstaller."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def carpeta_datos():
    """Carpeta raíz para los datos generados."""
    if _es_ejecutable():
        base = Path.home() / 'PSO_RNA_Suite'
    else:
        base = Path.cwd()
    base.mkdir(parents=True, exist_ok=True)
    return base


def carpeta_resultados_pso():
    ruta = carpeta_datos() / 'resultados_pso'
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def carpeta_logs():
    ruta = carpeta_resultados_pso() / 'logs'
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def carpeta_exportaciones():
    ruta = carpeta_datos() / 'exportaciones'
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def archivo_historial():
    return carpeta_resultados_pso() / 'historial_ejecuciones.json'


def archivo_historial_enjambre():
    return carpeta_resultados_pso() / 'Historial_Enjambre.csv'


def archivo_grafica():
    return carpeta_resultados_pso() / 'grafica_enjambre.png'