from abc import ABC, abstractmethod
import numpy as np

class BaseSurrogate(ABC):
    """
    Clase base para todos los modelos auxiliares del módulo MASA.
    """
    @abstractmethod
    def fit(self, X, y):
        """Entrena el modelo con los datos reales."""
        pass

    @abstractmethod
    def predict(self, X, return_std=False):
        pass

    @abstractmethod
    def generate_synthetic_data(self, n_samples, bounds):
        """
        Genera un dataset sintético.
        :param n_samples: Número de muestras a generar.
        :param bounds: Lista de tuplas con (min, max) para cada característica.
        :return: Tupla (X_sint, y_sint).
        """
        pass