"""Tests del parser seguro de funciones objetivo (PSO_MV/funcion_objetivo.py).

Verifica:
- Que las expresiones matemáticas válidas se compilan y evalúan bien.
- Que las expresiones con nodos prohibidos (atributos, lambdas, subscripts)
  se rechazan.
- Que las funciones con dominio restringido (log, sqrt) validan sus argumentos.
- Que las expresiones inválidas (vacías, con sintaxis rota) se rechazan.
"""

import warnings

import pytest

from PSO_MV.funcion_objetivo import crear_funcion_objetivo


# ------------------------------------------------------------------
# Funciones válidas
# ------------------------------------------------------------------

def test_funcion_simple():
    f = crear_funcion_objetivo('x1**2 + x2**2', 2, [1, 1])
    assert f([3, 4]) == pytest.approx(25.0)


def test_funcion_constante():
    f = crear_funcion_objetivo('5', 1, [0])
    assert f([42]) == pytest.approx(5.0)


@pytest.mark.parametrize("expr, punto, esperado", [
    ('abs(x1)',  [-3], 3.0),
    ('cos(x1)',  [0],  1.0),
    ('exp(x1)',  [0],  1.0),
    ('log(x1)',  [1],  0.0),
    ('sin(x1)',  [0],  0.0),
    ('sqrt(x1)', [4],  2.0),
    ('tan(x1)',  [0],  0.0),
])
def test_funciones_permitidas(expr, punto, esperado):
    f = crear_funcion_objetivo(expr, 1, [1])
    assert f(punto) == pytest.approx(esperado)


def test_operadores_aritmeticos():
    f = crear_funcion_objetivo('x1 + x2 - x3 * x4 / x5', 5, [1] * 5)
    # x1 + x2 = 15 ; x3 * x4 / x5 = 2 ; 15 - 2 = 13
    assert f([10, 5, 2, 1, 1]) == pytest.approx(13.0)


def test_potencia_y_modulo():
    f = crear_funcion_objetivo('x1**2 % 7', 1, [1])
    assert f([5]) == pytest.approx(25.0 % 7)  # 4.0


def test_parentesis_y_unarios():
    f = crear_funcion_objetivo('-(x1 + x2)', 2, [1, 1])
    assert f([3, 4]) == pytest.approx(-7.0)


# ------------------------------------------------------------------
# Entradas inválidas: variables
# ------------------------------------------------------------------

def test_variable_invalida():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('y1 + x1', 2, [1, 1])


def test_variable_fuera_rango():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('x5', 3, [1, 1, 1])


def test_nv_invalido():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('x1', 0, [1])


# ------------------------------------------------------------------
# Dominios matemáticos
# ------------------------------------------------------------------

def test_log_dominio_invalido():
    f = crear_funcion_objetivo('log(x1)', 1, [1])
    with pytest.raises(ValueError):
        f([-1])


def test_sqrt_dominio_invalido():
    f = crear_funcion_objetivo('sqrt(x1)', 1, [1])
    with pytest.raises(ValueError):
        f([-4])


def test_punto_prueba_dominio_invalido():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('log(x1)', 1, [-1])


# ------------------------------------------------------------------
# Nodos y funciones prohibidas
# ------------------------------------------------------------------

def test_funcion_desconocida():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('foo(x1)', 1, [1])


def test_nodo_prohibido_atributo():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('x1.__class__', 1, [1])


def test_nodo_prohibido_lambda():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('(lambda: 1)(x1)', 1, [1])


def test_nodo_prohibido_subscript():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('[1,2][0] + x1', 1, [1])


# ------------------------------------------------------------------
# Sintaxis y resultados inválidos
# ------------------------------------------------------------------

def test_expresion_vacia():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('', 1, [1])


def test_sintaxis_invalida():
    with pytest.raises(ValueError):
        crear_funcion_objetivo('x1 +', 1, [1])


def test_resultado_no_finito():
    f = crear_funcion_objetivo('exp(x1)', 1, [0])
    # exp(1e10) desborda a inf y debe ser rechazado
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ValueError):
            f([1e10])