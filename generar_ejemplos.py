# generar_ejemplos.py
"""Genera archivos de ejemplo para probar la importación.

Se ejecuta una sola vez. Los archivos quedan en ejemplos/.
"""

from pathlib import Path

import pandas as pd


CARPETA = Path('ejemplos')
CARPETA.mkdir(exist_ok=True)


# ----------------------------------------------------------------------
# Parámetros PSO
# ----------------------------------------------------------------------

filas_params = [
    ('NV',      '3'),
    ('NP',      '30'),
    ('NI',      '50'),
    ('FUNCION', 'x1**2 + x2**2 + x3**2'),
    ('OPT',     'Minimización'),
    ('D_W',     'True'),
    ('P_T',     'False'),
    ('HIST',    'True'),
    ('MIN_0',   '-5'), ('MAX_0', '5'),
    ('MIN_1',   '-5'), ('MAX_1', '5'),
    ('MIN_2',   '-5'), ('MAX_2', '5'),
]
df_params = pd.DataFrame(filas_params, columns=['parametro', 'valor'])
df_params.to_csv(CARPETA / 'parametros_pso.csv', index=False, encoding='utf-8')
df_params.to_excel(CARPETA / 'parametros_pso.xlsx', index=False, sheet_name='Parametros')


# ----------------------------------------------------------------------
# Datos RNA
# ----------------------------------------------------------------------

filas_datos = [
    (-2.34, 1.87, 9.03),  (-1.56, 2.43, 8.34), (-0.92, -1.78, 4.01),
    (0.45, 1.23, 1.72),   (1.87, -2.45, 9.50), (2.11, 0.87, 5.21),
    (-2.02, -0.34, 4.20), (0.98, 2.12, 5.45),  (-1.23, 1.45, 3.61),
    (1.56, -1.87, 5.93),  (-0.34, -2.12, 4.61),(2.45, 0.92, 6.85),
    (-1.87, 2.11, 7.94),  (0.87, -1.56, 3.19), (-2.11, -1.23, 5.97),
    (1.23, 1.87, 5.01),   (-0.87, 0.45, 0.96), (2.12, -0.98, 5.45),
    (-1.45, -2.11, 6.55), (0.34, 1.56, 2.55),  (1.78, 2.34, 8.65),
    (-2.45, 0.87, 6.76),  (0.92, -2.11, 5.30), (-1.78, -1.45, 5.27),
    (2.34, 1.45, 7.58),   (-0.45, 2.11, 4.65), (1.45, -0.87, 2.86),
    (-2.12, 1.56, 6.93),  (0.45, -1.23, 1.72), (1.87, 1.78, 6.68),
    (-1.56, -0.45, 2.63), (2.11, 2.12, 8.95),  (-0.92, 0.92, 1.69),
    (1.23, -2.34, 6.99),  (-2.34, -1.87, 8.97),(0.87, 1.45, 2.86),
    (-1.23, 2.34, 6.99),  (1.56, 0.34, 2.55),  (-0.34, -1.56, 2.55),
    (2.45, 1.23, 7.52),
]
df_datos = pd.DataFrame(filas_datos, columns=['x1', 'x2', 'y'])
df_datos.to_csv(CARPETA / 'datos_rna.csv', index=False, encoding='utf-8')
df_datos.to_excel(CARPETA / 'datos_rna.xlsx', index=False, sheet_name='Datos')


print('Archivos generados en', CARPETA.resolve())