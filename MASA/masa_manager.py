import pandas as pd
import numpy as np
import os
from .gpr_surrogate import GPRSurrogate

class MASAManager:
    def __init__(self, surrogate_model: GPRSurrogate):
        self.model = surrogate_model

    def _load_file(self, filepath):
        """Carga un archivo CSV o Excel de forma dinámica."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            return pd.read_csv(filepath)
        elif ext in ['.xls', '.xlsx']:
            return pd.read_excel(filepath)
        else:
            raise ValueError(f"Formato de archivo no soportado: {ext}. Use CSV o Excel.")

    def run_augmentation_pipeline(self, filepath, feature_cols, target_col, n_samples=50000, output_path="Dataset_Sintetico.csv"):
        """
        Ejecuta el pipeline de MASA con cualquier dataset.
        
        :param filepath: Ruta al archivo CSV o Excel.
        :param feature_cols: Lista con los nombres de las columnas de entrada (ej. ['PVA', 'MMT']).
        :param target_col: Nombre de la columna objetivo (ej. 'D').
        :param n_samples: Número de muestras sintéticas a generar.
        :param output_path: Ruta donde se guardará el nuevo dataset.
        """
        # 1. Cargar y validar datos
        df_real = self._load_file(filepath)
        
        # Validar que las columnas existan
        columnas_faltantes = [c for c in feature_cols + [target_col] if c not in df_real.columns]
        if columnas_faltantes:
            raise KeyError(f"Las siguientes columnas no se encontraron en el archivo: {columnas_faltantes}")

        # Eliminar filas con valores nulos en las columnas seleccionadas
        df_clean = df_real.dropna(subset=feature_cols + [target_col])
        
        X_real = df_clean[feature_cols].values
        y_real = df_clean[target_col].values

        # 2. Calcular Bounds Dinámicos (límites min y max de los datos reales)
        # Añadimos un pequeño margen del 5% para que el modelo explore un poco más allá
        bounds = []
        for i in range(X_real.shape[1]):
            min_val = X_real[:, i].min()
            max_val = X_real[:, i].max()
            margen = (max_val - min_val) * 0.05
            bounds.append((min_val - margen, max_val + margen))

        # 3. Entrenar el modelo auxiliar
        print("Entrenando modelo auxiliar...")
        self.model.fit(X_real, y_real)

        # 4. Generar datos sintéticos
        print(f"Generando {n_samples} muestras sintéticas...")
        X_sint, y_sint = self.model.generate_synthetic_data(n_samples, bounds)

        # 5. Construir el DataFrame sintético con los nombres originales
        df_sint = pd.DataFrame(X_sint, columns=feature_cols)
        df_sint[target_col] = y_sint
        
        # Opcional: Añadir una columna para identificar que son datos sintéticos
        df_sint['es_sintetico'] = True

        # 6. Guardar
        df_sint.to_csv(output_path, index=False)
        print(f"✅ Dataset exportado en: {output_path}")

        return {
            "status": "success",
            "n_synthetic_samples": n_samples,
            "output_path": output_path,
            "bounds_usados": bounds,
            "columnas": {"features": feature_cols, "target": target_col}
        }