import numpy as np
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from .base_surrogate import BaseSurrogate
from scipy.stats import qmc

class PolynomialSurrogate(BaseSurrogate):
    def __init__(self, degree=2, alpha=1.0, random_state=42):
        # Usamos Ridge (Regresión Lineal con regularización L2) 
        # para evitar sobreajuste cuando el dataset es pequeño.
        self.pipeline = make_pipeline(
            StandardScaler(),
            PolynomialFeatures(degree=degree, include_bias=False),
            Ridge(alpha=alpha, random_state=random_state)
        )
        self.y_min = None
        self.y_max = None

    def fit(self, X, y):
        self.y_min = np.min(y)
        self.y_max = np.max(y)
        self.pipeline.fit(X, y)
        return self

    def predict(self, X, return_std=False):
        # Ridge por defecto no calcula la incertidumbre (std) de forma nativa en predict,
        # así que devolvemos un array de ceros si se solicita para mantener la compatibilidad.
        preds = self.pipeline.predict(X)
        if return_std:
            return preds, np.zeros_like(preds)
        return preds

    def generate_synthetic_data(self, n_samples, bounds):
        lower_bounds = np.array([b[0] for b in bounds])
        upper_bounds = np.array([b[1] for b in bounds])
        
        # Muestreo con Hipercubo Latino
        sampler = qmc.LatinHypercube(d=len(bounds))
        sample = sampler.random(n=n_samples)
        X_sint = qmc.scale(sample, lower_bounds, upper_bounds)
        
        y_sint = self.predict(X_sint)
        
        # Recortar para que no se salga de los límites físicos de los datos reales
        y_sint = np.clip(y_sint, self.y_min, self.y_max)
        
        return X_sint, y_sint