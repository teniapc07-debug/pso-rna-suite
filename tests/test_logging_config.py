"""Tests del módulo de logging (logica/logging_config.py)."""

import json
import logging
from pathlib import Path

import pytest

from logica import logging_config


@pytest.fixture
def limpiar_handlers():
    """Elimina todos los handlers del logger raíz antes y después del test."""
    raiz = logging.getLogger()
    handlers_originales = list(raiz.handlers)
    for h in handlers_originales:
        raiz.removeHandler(h)
    yield
    for h in list(raiz.handlers):
        raiz.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
    for h in handlers_originales:
        raiz.addHandler(h)


@pytest.fixture
def carpeta_logs_temporal(tmp_path, monkeypatch):
    """Redirige CARPETA_LOGS a una carpeta temporal por test."""
    carpeta = tmp_path / 'logs'
    monkeypatch.setattr(logging_config, 'CARPETA_LOGS', carpeta)
    return carpeta


@pytest.fixture
def sin_archivo_config(monkeypatch, tmp_path):
    """Simula que logging_config.json no existe."""
    monkeypatch.setattr(logging_config, 'ARCHIVO_CONFIG', tmp_path / 'no_existe.json')


# ------------------------------------------------------------------
# Carga de configuración
# ------------------------------------------------------------------

def test_defaults_cuando_no_hay_archivo(sin_archivo_config):
    cfg = logging_config._cargar_config()
    assert cfg['nivel_archivo'] == 'DEBUG'
    assert cfg['nivel_gui'] == 'INFO'
    assert 'silenciar' in cfg


def test_fallback_con_json_corrupto(monkeypatch, tmp_path):
    archivo = tmp_path / 'roto.json'
    archivo.write_text('{ esto no es JSON }', encoding='utf-8')
    monkeypatch.setattr(logging_config, 'ARCHIVO_CONFIG', archivo)

    cfg = logging_config._cargar_config()
    assert cfg == logging_config.CONFIG_POR_DEFECTO


def test_mezcla_con_defaults(monkeypatch, tmp_path):
    archivo = tmp_path / 'cfg.json'
    archivo.write_text(json.dumps({'nivel_gui': 'WARNING'}), encoding='utf-8')
    monkeypatch.setattr(logging_config, 'ARCHIVO_CONFIG', archivo)

    cfg = logging_config._cargar_config()
    assert cfg['nivel_gui'] == 'WARNING'
    assert cfg['nivel_archivo'] == 'DEBUG'   # default conservado


# ------------------------------------------------------------------
# operacion_log
# ------------------------------------------------------------------

def test_operacion_log_crea_archivo(limpiar_handlers, carpeta_logs_temporal):
    with logging_config.operacion_log('test') as ruta:
        assert ruta.exists()


def test_operacion_log_escribe_mensajes(limpiar_handlers, carpeta_logs_temporal):
    logging_config.configurar_logging()
    logger = logging.getLogger('test_logger')
    with logging_config.operacion_log('test'):
        logger.info("mensaje de prueba")

    archivos = list(carpeta_logs_temporal.glob('*.log'))
    assert len(archivos) == 1
    contenido = archivos[0].read_text(encoding='utf-8')
    assert "mensaje de prueba" in contenido
    assert "Inicio de operación: test" in contenido
    assert "Fin de operación: test" in contenido


def test_operacion_log_cierra_handler(limpiar_handlers, carpeta_logs_temporal):
    raiz = logging.getLogger()
    handlers_antes = len(raiz.handlers)
    with logging_config.operacion_log('test'):
        assert len(raiz.handlers) > handlers_antes
    assert len(raiz.handlers) == handlers_antes


# ------------------------------------------------------------------
# GUIHandler
# ------------------------------------------------------------------

def test_gui_handler_sin_ventana_no_falla():
    handler = logging_config.GUIHandler(window=None, key='x')
    record = logging.LogRecord(
        name='t', level=logging.INFO, pathname='', lineno=0,
        msg='hola', args=(), exc_info=None,
    )
    handler.setFormatter(logging.Formatter('%(message)s'))
    # No debe lanzar excepción aunque window sea None
    handler.emit(record)