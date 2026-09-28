# logica/pso_runner.py
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import PySimpleGUI as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from PSO_MV import Enjambre_M
from PSO_MV import funcion_objetivo as modulo_funcion_objetivo
from RNA import Hibrido
from estado import estado, OutputGUI


# ---------------------------------------------------------------
# Gráfica
# ---------------------------------------------------------------
def actualizar_grafica(window, dtframe):
    if dtframe is None or dtframe.empty:
        return
    col_valor = None
    for nombre in ['Mejor_Valor', 'Mejor Valor Enjambre']:
        if nombre in dtframe.columns:
            col_valor = nombre
            break
    if col_valor is None:
        return
    valores = dtframe[col_valor].to_numpy(dtype=float)
    col_iter = None
    for nombre in ['Iteracion', 'Iteración']:
        if nombre in dtframe.columns:
            col_iter = nombre
            break
    iteraciones = (dtframe[col_iter].astype(int).to_numpy()
                   if col_iter is not None
                   else np.arange(1, len(valores) + 1))

    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
    ax.plot(iteraciones, valores, marker='o', linestyle='-', color='b')
    ax.set_title('Evolución del mejor valor del enjambre')
    ax.set_xlabel('Iteración')
    ax.set_ylabel('Mejor valor')
    ax.grid(True, alpha=0.3)

    canvas_tk = window['pso-CANVAS-'].Widget
    for child in canvas_tk.winfo_children():
        child.destroy()
    FigureCanvasTkAgg(fig, master=canvas_tk).draw()
    FigureCanvasTkAgg(fig, master=canvas_tk).get_tk_widget().pack(
        side='top', fill='both', expand=1)


# ---------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------
def _guardar_defaults(values):
    for k, v in values.items():
        if k.startswith('pso-'):
            estado.defaults[k] = v


def handle(event, values, window):
    # --- Cambio de modo ---
    if event in ('pso-MODO_BASICO-', 'pso-MODO_IMPORTADO-'):
        modo_importado = bool(values['pso-MODO_IMPORTADO-'])
        estado.defaults['pso-MODO_BASICO-'] = not modo_importado
        estado.defaults['pso-MODO_IMPORTADO-'] = modo_importado
        window['pso-FRAME-0-'].update(visible=modo_importado)
        window['pso-FRAME-1-'].update(visible=not modo_importado)
        return None

    # --- Actualizar NV ---
    if event == 'pso-ACTUALIZAR-':
        try:
            nnv = int(values['pso-NV-'])
            if nnv < 1:
                sp.popup_error("El número de variables debe ser >= 1.")
                return None
        except ValueError:
            sp.popup_error("Ingrese un número entero válido para Nº Variables.")
            return None
        _guardar_defaults(values)
        estado.nv = nnv
        return 'REBUILD'

    # --- Ayuda ---
    if event == 'pso-AYUDA-':
        sp.popup(
            "Ingrese la función objetivo con x1, x2, ..., xn.\n\n"
            "Funciones: abs, exp, log, sqrt, sin, cos, tan.\n\n"
            "Ejemplo: sin(x1) + log(x2) - sqrt(x3).",
            title='Ayuda - Función Objetivo')
        return None

    # --- Controles avanzados ---
    if event == 'pso-CONTROLES-':
        _dialogo_avanzados()
        return None

    # --- Cargar modelo RNA ---
    if event == 'pso-CARGAR_RNA-':
        ruta = values.get('pso-RUTA_RNA-', '').strip()
        if not ruta:
            sp.popup_error('Seleccione la carpeta del modelo RNA.')
            return None
        try:
            f_pred, nv_rna, lim_inf, lim_sup = Hibrido.cargar_funcion_prediccion(ruta)
        except Exception as exc:
            sp.popup_error(f'Error al cargar el modelo RNA:\n{exc}')
            return None

        estado.funcion_objetivo_rna = f_pred
        estado.ruta_rna = ruta
        estado.nv = int(nv_rna)
        for i in range(nv_rna):
            estado.defaults[f'pso-MIN-{i}-'] = str(lim_inf[i])
            estado.defaults[f'pso-MAX-{i}-'] = str(lim_sup[i])

        # Rellenar parámetros PSO sugeridos (si config.json los tiene)
        try:
            import json
            cfg = json.loads((Path(ruta) / 'config.json').read_text(encoding='utf-8'))
            pso_cfg = cfg.get('pso', {})
            mapping = {
                'pso-NP-': 'NP', 'pso-NI-': 'NI', 'pso-OPT-': 'OPT',
                'pso-W_I-': 'W_I', 'pso-W_F-': 'W_F', 'pso-C1-': 'C1',
                'pso-C2-': 'C2', 'pso-RONDAS-': 'RONDAS', 'pso-TOL-': 'TOL',
                'pso-RED_W-': 'RED_W', 'pso-P_T-': 'P_T',
            }
            for k_gui, k_cfg in mapping.items():
                if k_cfg in pso_cfg:
                    estado.defaults[k_gui] = pso_cfg[k_cfg]
        except Exception:
            pass

        window['pso-INFO_RNA-'].update(
            f'Modelo cargado desde: {ruta}\n'
            f'nv={nv_rna}\n'
            f'lim_inf={lim_inf}\n'
            f'lim_sup={lim_sup}\n'
            f'Listo para ejecutar PSO con esta función.'
        )
        return 'REBUILD'

    # --- Quitar modelo RNA ---
    if event == 'pso-QUITAR_RNA-':
        estado.funcion_objetivo_rna = None
        estado.ruta_rna = None
        window['pso-INFO_RNA-'].update('Modelo RNA descargado.\n'
                                       'Se usará la función simbólica.')
        return None

    # --- Importar CSV de parámetros ---
    if event == 'pso-IMPORTAR-':
        _importar_csv_params()
        return 'REBUILD'

    # --- Exportar CSV de parámetros ---
    if event == 'pso-EXPORTAR-':
        _exportar_csv_params()
        return None

    # --- Limpiar datos ---
    if event == 'pso-LIMPIAR-':
        _limpiar()
        return 'REBUILD'

    # --- Iniciar PSO ---
    if event == 'pso-INI-':
        _ejecutar_pso(values, window)
        return None

    return None


# ---------------------------------------------------------------
# Implementaciones auxiliares
# ---------------------------------------------------------------
def _dialogo_avanzados():
    sp_vals = {
        'pso-W_I-': '0.9', 'pso-W_F-': '0.4', 'pso-C1-': '1.5',
        'pso-C2-': '1.5', 'pso-RONDAS-': '10', 'pso-TOL-': '1e-6',
    }
    layout = [
        [sp.Text("Controles Avanzados", font=("Arial", 16, "bold"),
                 expand_x=True, justification='center')],
        [sp.Text("Inercia Inicial (w)", size=(24, 1)),
         sp.Input(key='pso-W_I-', size=(10, 1),
                  default_text=estado.defaults.get('pso-W_I-', '0.9'))],
        [sp.Text("Inercia Final (w)", size=(24, 1)),
         sp.Input(key='pso-W_F-', size=(10, 1),
                  default_text=estado.defaults.get('pso-W_F-', '0.4'))],
        [sp.Text("Coef. cognitivo (c1)", size=(24, 1)),
         sp.Input(key='pso-C1-', size=(10, 1),
                  default_text=estado.defaults.get('pso-C1-', '1.5'))],
        [sp.Text("Coef. social (c2)", size=(24, 1)),
         sp.Input(key='pso-C2-', size=(10, 1),
                  default_text=estado.defaults.get('pso-C2-', '1.5'))],
        [sp.Text("Rondas parada temprana", size=(24, 1)),
         sp.Input(key='pso-RONDAS-', size=(10, 1),
                  default_text=estado.defaults.get('pso-RONDAS-', '10'))],
        [sp.Text("Tolerancia parada temprana", size=(24, 1)),
         sp.Input(key='pso-TOL-', size=(10, 1),
                  default_text=estado.defaults.get('pso-TOL-', '1e-6'))],
        [sp.Button('Guardar', key='pso-GUARDAR_AV-', size=(12, 1)),
         sp.Button('Restablecer', key='pso-REST_AV-', size=(14, 1)),
         sp.Button('Cerrar', key='pso-CERRAR_AV-', size=(10, 1))],
    ]
    w = sp.Window('Controles Avanzados', layout, resizable=True, finalize=True)
    while True:
        ev, vals = w.read()
        if ev in (sp.WIN_CLOSED, 'pso-CERRAR_AV-'):
            break
        if ev == 'pso-GUARDAR_AV-':
            estado.defaults.update(vals)
            break
        if ev == 'pso-REST_AV-':
            estado.defaults.update(sp_vals)
            for k, v in sp_vals.items():
                w[k].update(value=v)
    w.close()


def _importar_csv_params():
    archivo = sp.popup_get_file('Seleccione CSV de parámetros',
                                file_types=(("CSV", "*.csv"),),
                                no_window=True)
    if not archivo:
        return
    try:
        df = pd.read_csv(archivo, dtype=str)
        if not {'parametro', 'valor'}.issubset(df.columns):
            raise ValueError("El CSV debe tener columnas 'parametro' y 'valor'.")
        p = dict(zip(df['parametro'].str.strip(),
                     df['valor'].fillna('').str.strip()))

        def to_bool(n):
            v = p.get(n, '').lower()
            if v not in {'true', 'false'}:
                raise ValueError(f'{n} debe ser True/False')
            return v == 'true'

        nv = int(p['NV'])
        if nv < 1:
            raise ValueError('NV debe ser >= 1.')
        estado.nv = nv
        estado.defaults.update({
            'pso-NP-': str(int(p['NP'])),
            'pso-NV-': str(nv),
            'pso-NI-': str(int(p['NI'])),
            'pso-FUNCION-': p['FUNCION'],
            'pso-OPT-': p['OPT'],
            'pso-D_W-': to_bool('D_W'),
            'pso-P_T-': to_bool('P_T'),
            'pso-HIST-': to_bool('HIST'),
        })
        for i in range(nv):
            estado.defaults[f'pso-MIN-{i}-'] = str(float(p[f'MIN_{i}']))
            estado.defaults[f'pso-MAX-{i}-'] = str(float(p[f'MAX_{i}']))
    except Exception as exc:
        sp.popup_error(f'Error al importar CSV:\n{exc}')


def _exportar_csv_params():
    archivo = sp.popup_get_file('Guardar CSV de parámetros',
                                save_as=True,
                                file_types=(("CSV", "*.csv"),),
                                no_window=True, default_extension='.csv')
    if not archivo:
        return
    # Asegurar carpeta resultados_pso
    carpeta = Path('resultados_pso')
    carpeta.mkdir(exist_ok=True)
    destino = Path(archivo)
    if destino.parent == Path('.'):
        destino = carpeta / destino.name
    try:
        with open(destino, 'w', encoding='utf-8') as f:
            f.write('parametro,valor\n')
            for k, v in estado.defaults.items():
                f.write(f'{k},{v}\n')
        sp.popup_ok(f'Datos exportados a {destino}')
    except Exception as exc:
        sp.popup_error(f'Error al exportar:\n{exc}')


def _limpiar():
    estado.nv = 0
    estado.funcion_objetivo_rna = None
    estado.ruta_rna = None
    estado.defaults = {
        'pso-MODO_BASICO-': True, 'pso-MODO_IMPORTADO-': False,
        'pso-OPT-': 'Minimización', 'pso-NP-': '', 'pso-NI-': '',
        'pso-FUNCION-': '', 'pso-D_W-': False, 'pso-HIST-': False,
        'pso-P_T-': False, 'pso-W_I-': '0.9', 'pso-W_F-': '0.4',
        'pso-C1-': '1.5', 'pso-C2-': '1.5', 'pso-RED_W-': True,
        'pso-RONDAS-': '10', 'pso-TOL-': '1e-6',
    }


def _ejecutar_pso(values, window):
    try:
        n_particulas  = int(values['pso-NP-'])
        n_iteraciones = int(values['pso-NI-'])
        nv_local      = int(values['pso-NV-'])
        lim_inf, lim_sup = [], []
        for i in range(nv_local):
            inf = float(values[f'pso-MIN-{i}-'])
            sup = float(values[f'pso-MAX-{i}-'])
            if inf >= sup:
                raise ValueError(f'Límite inf de x{i+1} >= sup.')
            lim_inf.append(inf); lim_sup.append(sup)

        punto_prueba = (np.array(lim_inf) + np.array(lim_sup)) / 2

        # ---- Elegir función objetivo ----
        if estado.funcion_objetivo_rna is not None:
            funcion_objetivo = estado.funcion_objetivo_rna
        else:
            funcion_objetivo = modulo_funcion_objetivo.crear_funcion_objetivo(
                values['pso-FUNCION-'], nv_local, punto_prueba)

        w_i = float(estado.defaults.get('pso-W_I-', '0.9'))
        w_f = float(estado.defaults.get('pso-W_F-', '0.4'))
        c1  = float(estado.defaults.get('pso-C1-', '1.5'))
        c2  = float(estado.defaults.get('pso-C2-', '1.5'))
        rondas_parada = int(estado.defaults.get('pso-RONDAS-', '10'))
        tolerancia    = float(estado.defaults.get('pso-TOL-', '1e-6'))
        reduccion_w   = bool(estado.defaults.get('pso-RED_W-',
                                                 values['pso-D_W-']))
    except (ValueError, TypeError) as exc:
        sp.popup_error(f"Error en datos o función objetivo:\n{exc}")
        return

    optimizacion = values['pso-OPT-']
    parada_temprana = bool(estado.defaults.get('pso-P_T-', values['pso-P_T-']))

    enj = Enjambre_M.enjambre(
        n_variables=nv_local, n_particulas=n_particulas,
        lim_inf=lim_inf, lim_sup=lim_sup, info=False)

    try:
        enj.optimizar(
            n_iteraciones=n_iteraciones, optimizacion=optimizacion,
            funcion_objetivo=funcion_objetivo, w=w_i, c1=c1, c2=c2,
            w_i=w_i, w_f=w_f, reduccion_w=reduccion_w, info=False,
            parada_temprana=parada_temprana, rondas_parada=rondas_parada,
            tolerancia=tolerancia,
            carpeta_salida="resultados_pso",       # ← NUEVA CARPETA
        )
    except ValueError as exc:
        sp.popup_error(f"Una partícula salió del dominio:\n{exc}")
        return

    if values['pso-HIST-']:
        actualizar_grafica(window, enj.dtframe)