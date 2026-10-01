"""Configuración de logging estructurado.

Centraliza la política de logging del proyecto:

- Salida concurrente a archivo y a la GUI.
- Un archivo de log por operación (PSO o entrenamiento RNA).
- Configuración externa en ``logging_config.json`` con fallback silencioso.

Uso típico desde un runner::

    from logica.logging_config import operacion_log
    with operacion_log('pso'):
        logger.info("Iniciando PSO")

En ``app.py`` se llama una sola vez a ``configurar_logging(window, key)``
al arrancar la aplicación.
"""

import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


CARPETA_LOGS = Path('resultados_pso') / 'logs'
ARCHIVO_CONFIG = Path('logging_config.json')

CONFIG_POR_DEFECTO = {
    'nivel_archivo': 'DEBUG',
    'nivel_gui': 'INFO',
    'formato': '%(asctime)s %(levelname)-5s [%(name)s] %(message)s',
    'formato_fecha': '%Y-%m-%d %H:%M:%S',
    'silenciar': [
        'matplotlib',
        'matplotlib.font_manager',
        'tensorflow',
        'absl',
        'PIL',
        'urllib3',
    ],
}

_logger_raiz = logging.getLogger()
_gui_handler = None


# ----------------------------------------------------------------------
# Carga de configuración
# ----------------------------------------------------------------------

def _cargar_config():
    """Carga ``logging_config.json`` con fallback silencioso a defaults.

    Si el archivo no existe, no es JSON válido o le faltan claves, se
    devuelve la configuración por defecto sin emitir error. El logging
    nunca debe romper el flujo normal de la aplicación.
    """
    if not ARCHIVO_CONFIG.exists():
        return dict(CONFIG_POR_DEFECTO)
    try:
        with open(ARCHIVO_CONFIG, encoding='utf-8') as f:
            cfg = json.load(f)
        resultado = dict(CONFIG_POR_DEFECTO)
        resultado.update(cfg)
        return resultado
    except Exception:
        return dict(CONFIG_POR_DEFECTO)


def _nivel(nombre, por_defecto):
    """Traduce un nombre de nivel a su valor numérico, con fallback."""
    if not isinstance(nombre, str):
        return por_defecto
    valor = getattr(logging, nombre.upper(), None)
    return valor if isinstance(valor, int) else por_defecto


# ----------------------------------------------------------------------
# Handler para GUI
# ----------------------------------------------------------------------

class GUIHandler(logging.Handler):
    """Handler que escribe al multiline de PySimpleGUI.

    Acumula los mensajes en un buffer y actualiza el widget con el
    contenido completo en cada emisión, igual que ``OutputGUI``.
    """

    def __init__(self, window, key):
        super().__init__()
        self.window = window
        self.key = key
        self.buffer = ''

    def emit(self, record):
        try:
            self.buffer += self.format(record) + '\n'
            self.window[self.key].update(self.buffer)
        except Exception:
            # Nunca propagar errores desde el handler: bloquearía la app.
            pass


# ----------------------------------------------------------------------
# Configuración inicial
# ----------------------------------------------------------------------

def configurar_logging(window=None, output_key=None):
    """Configura el logging raíz al arrancar la app o tras un REBUILD.

    - Ajusta el nivel del logger raíz a DEBUG (los handlers filtran).
    - Silencia loggers ruidosos según ``logging_config.json``.
    - Instala o reemplaza el ``GUIHandler`` si se pasa ``window``.
    - Fija ``TF_CPP_MIN_LOG_LEVEL`` a 2 si no está ya definida.

    No crea archivo de log: eso se hace en ``operacion_log``.
    """
    global _gui_handler
    cfg = _cargar_config()

    _logger_raiz.setLevel(logging.DEBUG)

    # Silenciar loggers ruidosos
    for nombre in cfg.get('silenciar', []):
        if isinstance(nombre, str):
            logging.getLogger(nombre).setLevel(logging.WARNING)

    # Instalar GUIHandler (reemplaza el anterior si existe)
    if window is not None and output_key is not None:
        if _gui_handler is not None:
            try:
                _logger_raiz.removeHandler(_gui_handler)
            except Exception:
                pass
        handler = GUIHandler(window, output_key)
        handler.setLevel(_nivel(cfg.get('nivel_gui'), logging.INFO))
        handler.setFormatter(logging.Formatter('%(message)s'))
        _logger_raiz.addHandler(handler)
        _gui_handler = handler

    # Silenciar TensorFlow (a nivel de proceso)
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')


# ----------------------------------------------------------------------
# Context manager por operación
# ----------------------------------------------------------------------

@contextmanager
def operacion_log(nombre_operacion):
    """Crea un archivo de log para una operación y lo elimina al salir.

    El archivo se nombra ``run_YYYYMMDD_HHMMSS_<nombre_operacion>.log``
    dentro de ``resultados_pso/logs/``.

    Al entrar:
      - Se crea la carpeta si no existe.
      - Se añade un ``FileHandler`` al logger raíz.
      - Se registra el inicio de la operación en nivel INFO.

    Al salir:
      - Se registra el fin de la operación en nivel INFO.
      - Se cierra y elimina el handler.

    Uso::

        with operacion_log('pso') as ruta_log:
            logger.info("...")
    """
    cfg = _cargar_config()
    CARPETA_LOGS.mkdir(parents=True, exist_ok=True)

    marca = datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo = CARPETA_LOGS / f"run_{marca}_{nombre_operacion}.log"

    handler = logging.FileHandler(archivo, encoding='utf-8')
    handler.setLevel(_nivel(cfg.get('nivel_archivo'), logging.DEBUG))
    handler.setFormatter(logging.Formatter(
        cfg.get('formato', CONFIG_POR_DEFECTO['formato']),
        datefmt=cfg.get('formato_fecha', CONFIG_POR_DEFECTO['formato_fecha']),
    ))

    _logger_raiz.addHandler(handler)
    logger = logging.getLogger(__name__)
    logger.info(f"Inicio de operación: {nombre_operacion}")
    logger.info(f"Log en: {archivo}")

    try:
        yield archivo
    finally:
        logger.info(f"Fin de operación: {nombre_operacion}")
        handler.close()
        _logger_raiz.removeHandler(handler)