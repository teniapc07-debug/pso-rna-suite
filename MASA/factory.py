# MASA/factory.py
from .gpr_surrogate import GPRSurrogate
from .poly_surrogate import PolynomialSurrogate

def obtener_surrogate(nombre_modelo):
    nombre = nombre_modelo.lower()
    if "gaussiano" in nombre or "gpr" in nombre:
        return GPRSurrogate()
    elif "polinomial" in nombre or "lineal" in nombre:
        return PolynomialSurrogate(degree=2)
    else:
        # Por defecto, devolver el GPR
        return GPRSurrogate()