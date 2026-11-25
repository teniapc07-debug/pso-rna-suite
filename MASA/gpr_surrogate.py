import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.preprocessing import StandardScaler
from .base_surrogate import BaseSurrogate

class GPRSurrogate(BaseSurrogate):
    def __init__(self, kernel=None, random_state=42):
        if kernel is None:
            kernel = ConstantKernel(1.0, (1e-2, 1e2)) * Matern(
                length_scale=1.0, length_scale_bounds=(0.1, 10.0), nu=1.5
            ) + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-5, 0.1))
        
        self.scaler_X = StandardScaler()
        self.gpr = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            n_restarts_optimizer=20,
            random_state=random_state
        )
        self.y_min = None
        self.y_max = None

    def fit(self, X, y):
        self.y_min = np.min(y)
        self.y_max = np.max(y)
        
        X_scaled = self.scaler_X.fit_transform(X)
        self.gpr.fit(X_scaled, y)
        return self

    def predict(self, X, return_std=False):
        X_scaled = self.scaler_X.transform(X)
        return self.gpr.predict(X_scaled, return_std=return_std)

    def generate_synthetic_data(self, n_samples, bounds):
        """
        Genera datos sintéticos basados en los bounds dinámicos.
        :param bounds: Lista de tuplas [(min, max), (min, max), ...] para cada feature.
        """
        lower_bounds = np.array([b[0] for b in bounds])
        upper_bounds = np.array([b[1] for b in bounds])
        
        # Generación con Hipercubo Latino para mejor cobertura del espacio
        from scipy.stats import qmc
        sampler = qmc.LatinHypercube(d=len(bounds))
        sample = sampler.random(n=n_samples)
        X_sint = qmc.scale(sample, lower_bounds, upper_bounds)
        
        y_sint = self.predict(X_sint)
        
        # Recortar predicciones al rango de los datos reales (evita valores negativos absurdos)
        y_sint = np.clip(y_sint, self.y_min, self.y_max)
        
        return X_sint, y_sint