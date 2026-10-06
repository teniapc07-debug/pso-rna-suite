# Carga un modelo exportado por RNAGUI.py y devuelve una función de predicción
# lista para usarse como función objetivo del PSO.
import json
from pathlib import Path

import joblib as jb
import numpy as np
import tensorflow as tf


def cargar_funcion_prediccion(carpeta_modelo):
    """
    Carga un modelo entrenado por RNAGUI.py desde una carpeta que contiene:
      - modelo.keras
      - scaler_x.save
      - scaler_y.save
      - config.json  (nv, lim_inf, lim_sup, columnas_x, [origen])

    Devuelve:
      funcion_prediccion(x) -> float
      nv        (int)
      lim_inf   (list[float])
      lim_sup   (list[float])
      origen    (dict | None)  — metadatos del entrenamiento si existen
    """
    carpeta = Path(carpeta_modelo)
    modelo_path = carpeta / 'modelo.keras'
    scaler_x_path = carpeta / 'scaler_x.save'
    scaler_y_path = carpeta / 'scaler_y.save'
    config_path = carpeta / 'config.json'

    for ruta in (modelo_path, scaler_x_path, scaler_y_path, config_path):
        if not ruta.exists():
            raise FileNotFoundError(f'No se encontró el archivo requerido: {ruta}')

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    modelo = tf.keras.models.load_model(modelo_path)
    scaler_x = jb.load(scaler_x_path)
    scaler_y = jb.load(scaler_y_path)

    nv = int(config['nv'])
    lim_inf = [float(v) for v in config['lim_inf']]
    lim_sup = [float(v) for v in config['lim_sup']]
    origen = config.get('origen')

    def funcion_prediccion(x):
        x_pr = np.array(x, dtype=float).reshape(1, -1)
        x_pr_sca = scaler_x.transform(x_pr)
        y_pr_sca = modelo.predict(x_pr_sca, verbose=0)
        y_pr = scaler_y.inverse_transform(y_pr_sca)
        return float(y_pr.flatten()[0])

    return funcion_prediccion, nv, lim_inf, lim_sup, origen