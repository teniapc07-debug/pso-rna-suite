"""Buscador de modelos RNA disponibles en el proyecto.

Escanea el árbol de directorios buscando carpetas que contengan un
``config.json`` válido de tipo ``"RNA"`` y los tres archivos auxiliares
del modelo. Devuelve una lista ordenada por fecha de modificación
descendente (más reciente primero).

Funciones puras, sin dependencia de PySimpleGUI.
"""

import json
import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)

PROFUNDIDAD_MAXIMA = 4

CARPETAS_IGNORADAS = {
    '.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.vscode', '.idea', 'node_modules',
    'PSO_MV', 'RNA', 'ui', 'logica', 'tests',
    'resultados_pso',
}

ARCHIVOS_REQUERIDOS = ('modelo.keras', 'scaler_x.save', 'scaler_y.save')


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _profundidad(ruta, raiz):
    """Cuenta cuántos niveles hay entre ``raiz`` y ``ruta``."""
    try:
        rel = ruta.relative_to(raiz)
    except ValueError:
        return 999
    return len(rel.parts)


def _es_carpeta_ignorada(ruta):
    return any(part in CARPETAS_IGNORADAS for part in ruta.parts)


def _validar_modelo(carpeta):
    """Verifica que una carpeta contiene un modelo RNA completo.

    Devuelve un dict con metadata si es válido, ``None`` en caso contrario.
    """
    try:
        config_path = carpeta / 'config.json'
        if not config_path.is_file():
            return None
        cfg = json.loads(config_path.read_text(encoding='utf-8'))
        if cfg.get('tipo') != 'RNA':
            return None

        for nombre in ARCHIVOS_REQUERIDOS:
            if not (carpeta / nombre).is_file():
                logger.warning(f"Modelo incompleto en {carpeta}: falta {nombre}")
                return None

        mtime = max(
            (carpeta / nombre).stat().st_mtime
            for nombre in (*ARCHIVOS_REQUERIDOS, 'config.json')
        )
        return {
            'nombre': carpeta.name,
            'ruta': str(carpeta),
            'nv': int(cfg.get('nv', 0)),
            'mtime': mtime,
        }
    except Exception as exc:
        logger.warning(f"Error al validar modelo en {carpeta}: {exc}")
        return None


def _formato_display(modelo):
    """Genera el string que se muestra en el ComboBox."""
    fecha = datetime.fromtimestamp(modelo['mtime']).strftime('%d/%m %H:%M')
    return f"{modelo['nombre']} — nv={modelo['nv']} | {fecha}"


# ----------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------

def buscar_modelos_disponibles(raiz=None):
    """Escanea ``raiz`` buscando modelos RNA válidos.

    Devuelve una lista de dicts con claves:
      - ``nombre``: nombre de la carpeta
      - ``ruta``: ruta completa
      - ``nv``: número de variables del modelo
      - ``mtime``: timestamp de modificación
      - ``display``: string formateado para mostrar en el ComboBox

    Ordenados por ``mtime`` descendente.
    """
    if raiz is None:
        raiz = Path.cwd()
    else:
        raiz = Path(raiz).resolve()

    encontrados = []
    try:
        for config_path in raiz.rglob('config.json'):
            if _es_carpeta_ignorada(config_path):
                continue
            if _profundidad(config_path, raiz) > PROFUNDIDAD_MAXIMA:
                continue

            modelo = _validar_modelo(config_path.parent)
            if modelo is not None:
                modelo['display'] = _formato_display(modelo)
                encontrados.append(modelo)
    except Exception as exc:
        logger.error(f"Error escaneando modelos: {exc}")
        return []

    encontrados.sort(key=lambda m: m['mtime'], reverse=True)
    logger.info(f"Modelos encontrados: {len(encontrados)}")
    return encontrados


def resolver_ruta(valor_combo, modelos):
    """Dado el valor actual del ComboBox, devuelve la ruta del modelo.

    - Si el valor coincide con el ``display`` de algún modelo, devuelve su ruta.
    - Si no, se trata como una ruta manual introducida por el usuario.
    """
    valor = (valor_combo or '').strip()
    if not valor:
        return ''
    for modelo in modelos:
        if modelo['display'] == valor:
            return modelo['ruta']
    # Fallback: ruta escrita a mano
    return valor