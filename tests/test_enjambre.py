"""Tests del motor del enjambre (PSO_MV/Enjambre_M.py).

Verifica:
- Convergencia en problemas convexos conocidos (esfera).
- Activación de la parada temprana.
- Escritura del historial en CSV.
- Invocación del callback de iteración.
- Estructura del DataFrame resultante.
- Propagación de errores (optimización inválida, dominio inválido).
"""

import csv
from pathlib import Path

import pytest

from PSO_MV.Enjambre_M import enjambre
from PSO_MV.funcion_objetivo import crear_funcion_objetivo


CARPETA_SALIDA = "resultados_pso"


def _esfera(pos):
    return float(pos[0]**2 + pos[1]**2)


def _esfera_negativa(pos):
    return -float(pos[0]**2 + pos[1]**2)


# ------------------------------------------------------------------
# Convergencia
# ------------------------------------------------------------------

@pytest.mark.slow
def test_converge_a_origen_2d():
    enj = enjambre(
        n_particulas=20, n_variables=2,
        lim_inf=[-5, -5], lim_sup=[5, 5],
    )
    enj.optimizar(
        funcion_objetivo=_esfera,
        optimizacion='Minimización',
        n_iteraciones=50,
        carpeta_salida=CARPETA_SALIDA,
    )
    assert enj.valor_optimo < 0.5


@pytest.mark.slow
def test_converge_a_maximo_2d():
    enj = enjambre(
        n_particulas=20, n_variables=2,
        lim_inf=[-5, -5], lim_sup=[5, 5],
    )
    enj.optimizar(
        funcion_objetivo=_esfera_negativa,
        optimizacion='Maximización',
        n_iteraciones=50,
        carpeta_salida=CARPETA_SALIDA,
    )
    assert enj.valor_optimo > -0.5


# ------------------------------------------------------------------
# Parada temprana
# ------------------------------------------------------------------

@pytest.mark.slow
def test_parada_temprana_dispara():
    # Con función constante, la diferencia entre iteraciones es 0,
    # que es < tolerancia. Debe detenerse tras rondas_parada iteraciones.
    enj = enjambre(
        n_particulas=10, n_variables=2,
        lim_inf=[-1, -1], lim_sup=[1, 1],
    )
    enj.optimizar(
        funcion_objetivo=lambda pos: 1.0,
        optimizacion='Minimización',
        n_iteraciones=50,
        parada_temprana=True,
        rondas_parada=3,
        tolerancia=1e-1,
        carpeta_salida=CARPETA_SALIDA,
    )
    assert enj.iteracion_optimo < 20


# ------------------------------------------------------------------
# Historial en disco
# ------------------------------------------------------------------

@pytest.mark.slow
def test_historial_se_escribe():
    archivo = Path(CARPETA_SALIDA) / "Historial_Enjambre.csv"
    if archivo.exists():
        archivo.unlink()

    enj = enjambre(
        n_particulas=5, n_variables=2,
        lim_inf=[-1, -1], lim_sup=[1, 1],
    )
    enj.optimizar(
        funcion_objetivo=_esfera,
        optimizacion='Minimización',
        n_iteraciones=3,
        carpeta_salida=CARPETA_SALIDA,
    )

    assert archivo.exists()
    with open(archivo, encoding='utf-8') as f:
        filas = list(csv.DictReader(f))

    assert len(filas) == 3
    assert 'Iteracion' in filas[0]
    assert 'Mejor_Valor' in filas[0]
    assert 'Mejor_Posición' in filas[0]


# ------------------------------------------------------------------
# Callback de iteración
# ------------------------------------------------------------------

@pytest.mark.slow
def test_callback_iteracion_se_invoca():
    llamadas = []

    def callback(actual, total, mejor):
        llamadas.append((int(actual), int(total), float(mejor)))

    enj = enjambre(
        n_particulas=5, n_variables=2,
        lim_inf=[-1, -1], lim_sup=[1, 1],
    )
    enj.optimizar(
        funcion_objetivo=_esfera,
        optimizacion='Minimización',
        n_iteraciones=5,
        iteracion_callback=callback,
        carpeta_salida=CARPETA_SALIDA,
    )

    assert len(llamadas) == 5
    assert llamadas[0][0] == 1
    assert llamadas[-1][0] == 5
    assert llamadas[-1][1] == 5


# ------------------------------------------------------------------
# Estructura del DataFrame
# ------------------------------------------------------------------

@pytest.mark.slow
def test_dtframe_columnas_esperadas():
    enj = enjambre(
        n_particulas=5, n_variables=2,
        lim_inf=[-1, -1], lim_sup=[1, 1],
    )
    enj.optimizar(
        funcion_objetivo=_esfera,
        optimizacion='Minimización',
        n_iteraciones=3,
        carpeta_salida=CARPETA_SALIDA,
    )
    columnas = set(enj.dtframe.columns)
    assert {'Iteracion', 'Mejor_Valor', 'Mejor_Posición'}.issubset(columnas)


# ------------------------------------------------------------------
# Propagación de errores
# ------------------------------------------------------------------

@pytest.mark.slow
def test_optimizacion_invalida():
    enj = enjambre(
        n_particulas=3, n_variables=1,
        lim_inf=[-1], lim_sup=[1],
    )
    with pytest.raises(Exception):
        enj.optimizar(
            funcion_objetivo=lambda pos: pos[0]**2,
            optimizacion='Otro',
            n_iteraciones=2,
            carpeta_salida=CARPETA_SALIDA,
        )


@pytest.mark.slow
def test_dominio_invalido_propaga():
    f = crear_funcion_objetivo('log(x1)', 1, [1])
    enj = enjambre(
        n_particulas=10, n_variables=1,
        lim_inf=[-5], lim_sup=[5],
    )
    with pytest.raises(ValueError):
        enj.optimizar(
            funcion_objetivo=f,
            optimizacion='Minimización',
            n_iteraciones=5,
            carpeta_salida=CARPETA_SALIDA,
        )