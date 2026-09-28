# logica/rna_runner.py
from pathlib import Path
import json
import numpy as np
import pandas as pd
import PySimpleGUI as sg
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import joblib as jb

from PSO_MV import funcion_objetivo as modulo_funcion_objetivo
from estado import estado


def _dibujar_perdida(window, historial):
    fig, eje = plt.subplots(figsize=(6, 4), dpi=100)
    eje.plot(historial['loss'], label='Entrenamiento')
    if 'val_loss' in historial:
        eje.plot(historial['val_loss'], label='Validación')
    eje.set_title('Pérdida del modelo')
    eje.set_xlabel('Época'); eje.set_ylabel('Pérdida')
    eje.grid(True, alpha=0.3); eje.legend()
    fig.tight_layout()

    canvas = window['rna-CANVAS-'].Widget
    for h in canvas.winfo_children():
        h.destroy()
    fc = FigureCanvasTkAgg(fig, master=canvas)
    fc.draw()
    fc.get_tk_widget().pack(fill='both', expand=True)


def handle(event, values, window):
    # --- Cambio de modo ---
    if event in ('rna-MODO-SINTETICO-', 'rna-MODO-IMPORTADO-'):
        modo_imp = values['rna-MODO-IMPORTADO-']
        window['rna-FRAME-0-'].update(visible=not modo_imp)
        window['rna-FRAME-4-'].update(visible=modo_imp)
        window['rna-IMPORTAR-'].update(visible=modo_imp)
        return None

    # --- Importar CSV ---
    if event == 'rna-IMPORTAR-':
        _importar_csv(values, window)
        return None

    # --- Generar RNA ---
    if event == 'rna-GENERAR-':
        _generar_rna(values, window)
        return None

    # --- Predecir ---
    if event == 'rna-PREDICIR-':
        _predecir(values)
        return None

    # --- Exportar modelo ---
    if event == 'rna-EXPORTAR-':
        _exportar_modelo(values)
        return None

    return None


def _importar_csv(values, window):
    archivo = sg.popup_get_file('Seleccione un CSV',
                                file_types=(("CSV", "*.csv"),),
                                no_window=True)
    if not archivo:
        return
    try:
        df = pd.read_csv(archivo)
        if df.empty:
            raise ValueError('CSV vacío.')
        col_y = values.get('rna-COL_Y-') or df.columns[-1]
        if col_y not in df.columns:
            raise ValueError(f'Columna "{col_y}" no existe.')
        y = df[col_y].to_numpy(dtype=float)
        X = df.drop(columns=[col_y]).to_numpy(dtype=float)
        if X.shape[1] < 1:
            raise ValueError('Se requiere al menos una columna de entrada.')
        if np.isnan(X).any() or np.isnan(y).any():
            raise ValueError('Hay NaNs en el CSV.')

        columnas_x = [c for c in df.columns if c != col_y]
        estado.rna_datos_importados = {
            'X': X, 'y': y, 'archivo': archivo, 'columnas_x': columnas_x}
        estado.rna_nv = X.shape[1]

        window['rna-COL_Y-'].update(values=list(df.columns), value=col_y)
        window['rna-MODO-IMPORTADO-'].update(value=True)
        window['rna-FRAME-0-'].update(visible=False)
        window['rna-FRAME-4-'].update(visible=True)
        window['rna-ESTADO-'].update(
            f'CSV: {X.shape[0]} muestras, {X.shape[1]} entradas. '
            f'Salida "{col_y}".')
    except Exception as exc:
        estado.rna_datos_importados = None
        sg.popup_error(f'Error al importar CSV:\n{exc}')


def _generar_rna(values, window):
    # --- Recolectar entradas de X, y, nv ---
    if not values['rna-MODO-IMPORTADO-']:
        try:
            nv = int(values['rna-NV-'])
            lim_inf = [float(x) for x in values['rna-LIM_INF-'].split(',')]
            lim_sup = [float(x) for x in values['rna-LIM_SUP-'].split(',')]
            if nv < 1 or len(lim_inf) != nv or len(lim_sup) != nv:
                raise ValueError('nv ≠ cantidad de límites.')
            if any(i >= s for i, s in zip(lim_inf, lim_sup)):
                raise ValueError('Cada inf debe ser < sup.')
            estado.rna_lim_inf_global = list(lim_inf)
            estado.rna_lim_sup_global = list(lim_sup)
            estado.rna_columnas_x_global = [f'x{i+1}' for i in range(nv)]
            punto = (np.array(lim_inf) + np.array(lim_sup)) / 2
            func = modulo_funcion_objetivo.crear_funcion_objetivo(
                values['rna-FUNCION-'], nv, punto)
        except Exception as exc:
            sg.popup_error(f'Error en datos sintéticos: {exc}')
            return
    else:
        if estado.rna_datos_importados is None:
            sg.popup_error('Importe un CSV antes de generar la RNA.')
            return
        X = estado.rna_datos_importados['X']
        y = estado.rna_datos_importados['y']
        nv = X.shape[1]

    # --- Entradas de la RNA ---
    try:
        capas = int(values['rna-CAPAS-'])
        neuronas = [int(x) for x in values['rna-NEURONAS-'].split(',')]
        if len(neuronas) != capas:
            raise ValueError('Nº neuronas ≠ nº capas.')
        activacion = values['rna-ACTIVACION-']
        epocas = int(values['rna-EPOCAS-'])
        batch = int(values['rna-BATCH-'])
        muestras = int(values['rna-MUESTRAS-'])
        if min(capas, epocas, batch, muestras, *neuronas) < 1:
            raise ValueError('Todos los valores deben ser >= 1.')
    except Exception as exc:
        sg.popup_error(f'Error en la RNA: {exc}')
        return

    try:
        if estado.rna_datos_importados is None:
            X = np.random.uniform(lim_inf, lim_sup, size=(muestras, nv))
            y = np.array([func(p) for p in X], dtype=float)

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42)
        sx, sy = StandardScaler(), StandardScaler()
        X_train = sx.fit_transform(X_train); X_val = sx.transform(X_val)
        y_train = sy.fit_transform(y_train.reshape(-1, 1))
        y_val   = sy.transform(y_val.reshape(-1, 1))

        modelo = models.Sequential([layers.Input(shape=(nv,))])
        for n in neuronas:
            modelo.add(layers.Dense(n, activation=activacion))
        modelo.add(layers.Dense(1))
        modelo.compile(optimizer='adam', loss='mean_squared_error')

        window['rna-PROGRESO-'].update(current_count=0, max=epocas)
        window['rna-PORCENTAJE-'].update('0%')

        class _CB(tf.keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                p = epoch + 1
                window['rna-PROGRESO-'].update(current_count=p, max=epocas)
                window['rna-PORCENTAJE-'].update(f'{int(p*100/epocas)}%')
                window['rna-ESTADO-'].update(f'Entrenando época {p}/{epocas}…')
                window.refresh()

        hist = modelo.fit(X_train, y_train,
                          validation_data=(X_val, y_val),
                          epochs=epocas, batch_size=batch,
                          callbacks=[_CB()], verbose=0)
        _dibujar_perdida(window, hist.history)

        estado.rna_modelo = modelo
        estado.rna_escalador_x = sx
        estado.rna_escalador_y = sy
        estado.rna_X_validacion = X_val
        estado.rna_y_validacion = y_val
        estado.rna_nv = nv
        window['rna-ESTADO-'].update('Entrenamiento finalizado.')
    except Exception as exc:
        sg.popup_error(f'Error durante el entrenamiento: {exc}')
        window['rna-ESTADO-'].update('El entrenamiento terminó con errores.')


def _predecir(values):
    try:
        vals = [float(x) for x in values['rna-VALORES-'].split(',')]
        if len(vals) != estado.rna_nv:
            sg.popup_error(f'Ingrese exactamente {estado.rna_nv} valores.')
            return
        v_sc = estado.rna_escalador_x.transform([vals])
        pred_sc = estado.rna_modelo.predict(v_sc, verbose=0)
        pred = estado.rna_escalador_y.inverse_transform(pred_sc)
        loss = estado.rna_modelo.evaluate(
            estado.rna_X_validacion, estado.rna_y_validacion, verbose=0)
        sg.popup(f'Predicción: {pred[0][0]}\nPérdida validación: {loss:.6f}')
    except Exception as exc:
        sg.popup_error(f'Error en la predicción: {exc}')


def _exportar_modelo(values):
    if estado.rna_modelo is None:
        sg.popup_error('Primero entrene/gene la RNA antes de exportar.')
        return

    if values['rna-MODO-IMPORTADO-']:
        if estado.rna_datos_importados is None:
            sg.popup_error('No hay datos importados.')
            return
        X = estado.rna_datos_importados['X']
        lim_inf = X.min(axis=0).tolist()
        lim_sup = X.max(axis=0).tolist()
        nv_exp = X.shape[1]
        cols = estado.rna_datos_importados.get(
            'columnas_x', [f'x{i+1}' for i in range(nv_exp)])
    else:
        if estado.rna_lim_inf_global is None:
            sg.popup_error('No se encontraron límites.')
            return
        lim_inf = list(estado.rna_lim_inf_global)
        lim_sup = list(estado.rna_lim_sup_global)
        nv_exp = estado.rna_nv
        cols = estado.rna_columnas_x_global or [f'x{i+1}' for i in range(nv_exp)]

    carpeta = sg.popup_get_folder('Carpeta de exportación del modelo')
    if not carpeta:
        return
    try:
        c = Path(carpeta); c.mkdir(parents=True, exist_ok=True)
        estado.rna_modelo.save(c / 'modelo.keras')
        jb.dump(estado.rna_escalador_x, c / 'scaler_x.save')
        jb.dump(estado.rna_escalador_y, c / 'scaler_y.save')

        cfg = {
            'tipo': 'RNA', 'version': 1,
            'nv': int(nv_exp),
            'lim_inf': [float(v) for v in lim_inf],
            'lim_sup': [float(v) for v in lim_sup],
            'columnas_x': list(cols),
            'pso': {
                'NP': 30, 'NI': 50, 'OPT': 'Minimización',
                'W_I': 0.9, 'W_F': 0.4, 'C1': 1.5, 'C2': 1.5,
                'RONDAS': 10, 'TOL': 1e-6, 'RED_W': True, 'P_T': False,
            },
        }
        with open(c / 'config.json', 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        sg.popup(f'Modelo exportado en:\n{c}')
    except Exception as exc:
        sg.popup_error(f'Error al exportar: {exc}')