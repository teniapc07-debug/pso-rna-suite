"""Tests de la clase Partícula (PSO_MV/Particula_M.py).

Verifica:
- Inicialización dentro de los límites.
- Evaluación contra la función objetivo.
- Actualización de la mejor posición local.
- Respeto de límites al moverse.
- Rechazo de modos de optimización inválidos.
"""

import numpy as np
import pytest

from PSO_MV.Particula_M import particula


def test_inicializacion_dentro_limites():
    lim_inf = np.array([-5.0, -3.0])
    lim_sup = np.array([5.0, 3.0])
    p = particula(n_variables=2, lim_inf=lim_inf, lim_sup=lim_sup)
    assert np.all(p.posicion >= lim_inf)
    assert np.all(p.posicion <= lim_sup)


def test_evaluar_particula_min():
    p = particula(n_variables=2, lim_inf=[-1, -1], lim_sup=[1, 1])
    p.evaluar_particula(
        optimizacion='Minimización',
        funcion_objetivo=lambda pos: pos[0]**2 + pos[1]**2,
    )
    assert p.mej_valor == pytest.approx(p.valor)
    assert np.array_equal(p.mej_posicion, p.posicion)


def test_evaluar_particula_max():
    p = particula(n_variables=2, lim_inf=[-1, -1], lim_sup=[1, 1])
    p.evaluar_particula(
        optimizacion='Maximización',
        funcion_objetivo=lambda pos: -(pos[0]**2 + pos[1]**2),
    )
    assert p.mej_valor == pytest.approx(p.valor)


def test_mejora_local():
    p = particula(n_variables=1, lim_inf=[0], lim_sup=[10])
    p.posicion = np.array([5.0])
    p.evaluar_particula(
        optimizacion='Minimización',
        funcion_objetivo=lambda pos: pos[0],
    )
    valor_primero = float(p.mej_valor)

    p.posicion = np.array([2.0])
    p.evaluar_particula(
        optimizacion='Minimización',
        funcion_objetivo=lambda pos: pos[0],
    )
    assert float(p.mej_valor) < valor_primero
    assert float(p.mej_valor) == pytest.approx(2.0)


def test_actualizar_componentes_respeta_limites():
    p = particula(n_variables=2, lim_inf=[-1, -1], lim_sup=[1, 1])
    p.posicion = np.array([0.5, 0.5])
    p.velocidad = np.array([0.0, 0.0])
    p.mej_posicion = np.array([0.5, 0.5])
    p.mej_valor = 0.0
    # gbest fuera de rango para forzar clamping
    gbest = np.array([100.0, 100.0])
    p.actualizar_componentes(gbest_posicion=gbest, w=0.9, c1=1.5, c2=1.5)
    assert np.all(p.posicion <= np.array([1.0, 1.0]))
    assert np.all(p.posicion >= np.array([-1.0, -1.0]))


def test_optimizacion_invalida():
    p = particula(n_variables=1, lim_inf=[0], lim_sup=[1])
    with pytest.raises(Exception):
        p.evaluar_particula(
            optimizacion='Otro',
            funcion_objetivo=lambda pos: pos[0],
        )