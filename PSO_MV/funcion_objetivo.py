import ast

import numpy as np


_FUNCIONES_PERMITIDAS = {
    'abs': np.abs,
    'cos': np.cos,
    'exp': np.exp,
    'log': np.log,
    'sin': np.sin,
    'sqrt': np.sqrt,
    'tan': np.tan,
}

_CONDICIONES_DOMINIO = {
    'log': ('mayor que cero', lambda valor: valor > 0),
    'sqrt': ('mayor o igual que cero', lambda valor: valor >= 0),
}


class _ValidadorExpresion(ast.NodeVisitor):
    _nodos_permitidos = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.USub,
        ast.UAdd,
        ast.Constant,
        ast.Name,
        ast.Call,
    )

    def __init__(self, n_variables):
        self.n_variables = n_variables

    def generic_visit(self, node):
        if not isinstance(node, self._nodos_permitidos):
            raise ValueError('La expresión contiene una operación no permitida.')
        super().generic_visit(node)

    def visit_Name(self, node):
        nombres_variables = {
            f'x{i}' for i in range(1, self.n_variables + 1)
        }
        if node.id not in nombres_variables and node.id not in _FUNCIONES_PERMITIDAS:
            raise ValueError(
                f'Variable no válida: {node.id}. Use x1, x2, ..., x{self.n_variables}.'
            )

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCIONES_PERMITIDAS:
            raise ValueError('Solo se permiten funciones matemáticas conocidas.')
        if len(node.args) != 1 or node.keywords:
            raise ValueError('Las funciones matemáticas deben recibir un argumento.')
        self.generic_visit(node)


def crear_funcion_objetivo(expresion, n_variables, punto_prueba=None):
    """Compila, valida y devuelve una función objetivo definida por el usuario."""
    expresion = expresion.strip()
    if not expresion:
        raise ValueError('Ingrese una función objetivo.')
    if n_variables < 1:
        raise ValueError('El número de variables debe ser mayor que cero.')

    try:
        arbol = ast.parse(expresion, mode='eval')
    except SyntaxError as exc:
        raise ValueError('La función objetivo tiene una sintaxis inválida.') from exc

    _ValidadorExpresion(n_variables).visit(arbol)
    codigo = compile(arbol, '<funcion_objetivo>', 'eval')

    llamadas_con_dominio = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and nodo.func.id in _CONDICIONES_DOMINIO:
            codigo_argumento = compile(
                ast.Expression(nodo.args[0]), '<argumento_funcion>', 'eval'
            )
            llamadas_con_dominio.append((nodo.func.id, codigo_argumento))

    def funcion_objetivo(posicion):
        posicion = np.asarray(posicion, dtype=float)
        entorno = {
            f'x{i}': posicion[i - 1] for i in range(1, n_variables + 1)
        }
        entorno.update(_FUNCIONES_PERMITIDAS)
        try:
            for nombre_funcion, codigo_argumento in llamadas_con_dominio:
                argumento = eval(codigo_argumento, {'__builtins__': {}}, entorno)
                condicion = _CONDICIONES_DOMINIO[nombre_funcion][1]
                if not np.all(condicion(argumento)):
                    condicion_texto = _CONDICIONES_DOMINIO[nombre_funcion][0]
                    raise ValueError(
                        f'El argumento de {nombre_funcion} debe ser {condicion_texto}.'
                    )
            resultado = eval(codigo, {'__builtins__': {}}, entorno)
        except (ArithmeticError, TypeError, ValueError, IndexError) as exc:
            raise ValueError(f'No se pudo evaluar la función objetivo: {exc}') from exc

        resultado = np.asarray(resultado)
        if resultado.size != 1:
            raise ValueError('La función objetivo debe devolver un único valor.')
        resultado = float(resultado.reshape(-1)[0])
        if not np.isfinite(resultado):
            raise ValueError('La evaluación de la función no produjo un valor finito.')
        return resultado

    if punto_prueba is None:
        punto_prueba = np.ones(n_variables)
    funcion_objetivo(punto_prueba)
    return funcion_objetivo