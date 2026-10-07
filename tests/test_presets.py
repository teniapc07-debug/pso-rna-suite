"""Tests del módulo de presets para reentrenamiento (Punto 5).

Solo cubre la lógica aislada de `aplicar_presets`. El handoff completo
(PSO → RNA con cambio de tab) no se testea aquí.
"""

import pytest

from estado import estado
from logica import rna_runner


class _FakeElemento:
    """Mock de un widget de PySimpleGUI que registra updates."""
    def __init__(self, key):
        self.key = key
        self.ultimo_valor = None
        self.ultima_visibilidad = None
        self.ultimo_visible = None

    def update(self, value=None, visible=None, **kwargs):
        if value is not None:
            self.ultimo_valor = value
        if visible is not None:
            self.ultimo_visible = visible


class _FakeWindow:
    """Mock de window que soporta `window[key]`."""
    def __init__(self, keys):
        self._elementos = {k: _FakeElemento(k) for k in keys}

    def __getitem__(self, key):
        return self._elementos[key]


KEYS_ESPERADAS = [
    'rna-MODO-SINTETICO-', 'rna-MODO-IMPORTADO-',
    'rna-FRAME-0-', 'rna-FRAME-4-', 'rna-IMPORTAR-',
    'rna-FUNCION-', 'rna-NV-', 'rna-LIM_INF-', 'rna-LIM_SUP-',
    'rna-MUESTRAS-', 'rna-CAPAS-', 'rna-NEURONAS-',
    'rna-ACTIVACION-', 'rna-EPOCAS-', 'rna-BATCH-', 'rna-ESTADO-',
]


@pytest.fixture(autouse=True)
def limpiar_estado():
    estado.rna_presets = None
    yield
    estado.rna_presets = None


# ----------------------------------------------------------------------

def test_aplicar_presets_sin_datos_no_hace_nada():
    window = _FakeWindow(KEYS_ESPERADAS)
    rna_runner.aplicar_presets(window)
    # No se ha llamado a ningún update
    for key in KEYS_ESPERADAS:
        assert window[key].ultimo_valor is None


def test_aplicar_presets_sintetico():
    estado.rna_presets = {
        'modo': 'sintetico',
        'funcion': 'x1**2 + x2**2',
        'nv': 2,
        'lim_inf': [-5.0, -5.0],
        'lim_sup': [5.0, 5.0],
        'muestras': 5000,
        'capas': 3,
        'neuronas': [2, 64, 32],
        'activacion': 'sigmoid',
        'epocas': 1000,
        'batch': 64,
    }
    window = _FakeWindow(KEYS_ESPERADAS)
    rna_runner.aplicar_presets(window)

    assert window['rna-FUNCION-'].ultimo_valor == 'x1**2 + x2**2'
    assert window['rna-NV-'].ultimo_valor == '2'
    assert window['rna-LIM_INF-'].ultimo_valor == '-5.0, -5.0'
    assert window['rna-LIM_SUP-'].ultimo_valor == '5.0, 5.0'
    assert window['rna-MUESTRAS-'].ultimo_valor == '5000'
    assert window['rna-CAPAS-'].ultimo_valor == '3'
    assert window['rna-NEURONAS-'].ultimo_valor == '2, 64, 32'
    assert window['rna-ACTIVACION-'].ultimo_valor == 'sigmoid'
    assert window['rna-EPOCAS-'].ultimo_valor == '1000'
    assert window['rna-BATCH-'].ultimo_valor == '64'

    assert window['rna-MODO-SINTETICO-'].ultimo_visible is None  # se pasa por update(value=True)
    assert window['rna-FRAME-0-'].ultimo_visible is True
    assert window['rna-FRAME-4-'].ultimo_visible is False


def test_aplicar_presets_importado(monkeypatch):
    # Silenciar el popup informativo
    import FreeSimpleGUI as sg
    monkeypatch.setattr(sg, 'popup', lambda *a, **k: None)

    estado.rna_presets = {
        'modo': 'importado',
        'funcion': None,
        'nv': 3,
        'lim_inf': [],
        'lim_sup': [],
        'muestras': 1000,
        'capas': 2,
        'neuronas': [16, 8],
        'activacion': 'relu',
        'epocas': 100,
        'batch': 32,
    }
    window = _FakeWindow(KEYS_ESPERADAS)
    rna_runner.aplicar_presets(window)

    # No debe haber rellenado la función simbólica
    assert window['rna-FUNCION-'].ultimo_valor is None
    # Sí debe haber rellenado la arquitectura
    assert window['rna-CAPAS-'].ultimo_valor == '2'
    assert window['rna-NEURONAS-'].ultimo_valor == '16, 8'
    assert window['rna-EPOCAS-'].ultimo_valor == '100'
    # Modo importado activo
    assert window['rna-FRAME-0-'].ultimo_visible is False
    assert window['rna-FRAME-4-'].ultimo_visible is True


def test_aplicar_presets_no_consume_estado():
    """Tras aplicar, `estado.rna_presets` sigue disponible."""
    estado.rna_presets = {
        'modo': 'sintetico', 'funcion': 'x1', 'nv': 1,
        'lim_inf': [-1], 'lim_sup': [1],
        'muestras': 10, 'capas': 1, 'neuronas': [4],
        'activacion': 'relu', 'epocas': 1, 'batch': 1,
    }
    window = _FakeWindow(KEYS_ESPERADAS)
    rna_runner.aplicar_presets(window)
    assert estado.rna_presets is not None