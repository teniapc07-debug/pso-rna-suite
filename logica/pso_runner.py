# logica/pso_runner.py
import sys
from pathlib import Path
from estado import estado, OutputGUI
import json
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
def _embed_figure(window, fig):
    """Incrusta una figura matplotlib ya construida en el canvas del tab Resultados."""
    canvas_tk = window['res-CANVAS-'].Widget
    for child in canvas_tk.winfo_children():
        child.destroy()
    fc = FigureCanvasTkAgg(fig, master=canvas_tk)
    fc.draw()
    fc.get_tk_widget().pack(side='top', fill='both', expand=1)


def actualizar_grafica(window, dtframe):
    """Dibuja la evolución del mejor valor y guarda la figura en estado."""
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

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=100)
    ax.plot(iteraciones, valores, marker='o', linestyle='-', color='b')
    ax.set_title('Evolución del mejor valor del enjambre')
    ax.set_xlabel('Iteración')
    ax.set_ylabel('Mejor valor')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    # Persistir en el estado compartido
    estado.ultima_figura = fig
    estado.ultimo_dtframe = dtframe

    _embed_figure(window, fig)


# ---------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------
def _guardar_defaults(values):
    for k, v in values.items():
        if k.startswith('pso-'):
            estado.defaults[k] = v


def handle(event, values, window):
    if event == 'pso-EDITAR_CONFIG-':
        return _dialogo_editar_config()

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
            f'nv={nv_rna}  |  lim_inf={lim_inf}\n'
            f'lim_sup={lim_sup}\n'
            f'Se usará el modelo RNA como función objetivo.'
        )
        window['pso-PIN_EDITAR-'].update(visible=True)
        # Resetear progreso
        window['pso-ESTADO-'].update('Modelo RNA listo. Pulsa "Iniciar PSO".')
        window['pso-PROGRESO-'].update(current_count=0, max=1)
        window['pso-PORCENTAJE-'].update('0%')
        return 'REBUILD'

    # --- Quitar modelo RNA ---
    if event == 'pso-QUITAR_RNA-':
        estado.funcion_objetivo_rna = None
        estado.ruta_rna = None
        window['pso-INFO_RNA-'].update(
            'No hay modelo RNA cargado. Se usará la función simbólica.')
        window['pso-PIN_EDITAR-'].update(visible=False)
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

        if estado.funcion_objetivo_rna is not None:
            funcion_objetivo = estado.funcion_objetivo_rna
            origen = 'modelo RNA'
        else:
            funcion_objetivo = modulo_funcion_objetivo.crear_funcion_objetivo(
                values['pso-FUNCION-'], nv_local, punto_prueba)
            origen = 'función simbólica'

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

    # --- Preparar UI de progreso ---
    window['pso-PROGRESO-'].update(current_count=0, max=n_iteraciones)
    window['pso-PORCENTAJE-'].update('0%')
    window['pso-ESTADO-'].update(
        f'Iniciando PSO ({origen}) — {n_particulas} partículas × {n_iteraciones} iteraciones…')
    window.refresh()

    def _on_iteracion(actual, total, mejor_valor):
        try:
            pct = int(actual * 100 / total)
            window['pso-PROGRESO-'].update(current_count=actual, max=total)
            window['pso-PORCENTAJE-'].update(f'{pct}%')
            window['pso-ESTADO-'].update(
                f'Iteración {actual}/{total} — mejor valor: {float(mejor_valor):.6g}')
            window.refresh()
        except Exception:
            pass

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
            carpeta_salida="resultados_pso",
            iteracion_callback=_on_iteracion,       # ← NUEVO
        )
    except ValueError as exc:
        sp.popup_error(f"Una partícula salió del dominio:\n{exc}")
        window['pso-ESTADO-'].update('Error durante la ejecución.')
        return

    # --- Estado final ---
    try:
        mejor = float(enj.valor_optimo)
        window['pso-ESTADO-'].update(
            f'Completado ({enj.iteracion_optimo} iters) — mejor valor: {mejor:.6g}')
        window['pso-PROGRESO-'].update(current_count=enj.iteracion_optimo,
                                       max=enj.iteracion_optimo)
        window['pso-PORCENTAJE-'].update('100%')
    except Exception:
        pass

    if values['pso-HIST-']:
        actualizar_grafica(window, enj.dtframe)


def guardar_grafica_png(window):
    """Guarda la última figura en resultados_pso/grafica_enjambre.png."""
    if estado.ultima_figura is None:
        sp.popup_error('Todavía no hay gráfica para guardar. Ejecuta primero el PSO con '
                       '"Gráfica de Historial" marcada.')
        return
    carpeta = Path('resultados_pso')
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / 'grafica_enjambre.png'
    try:
        estado.ultima_figura.savefig(ruta, dpi=150, bbox_inches='tight')
        sp.popup_ok(f'Gráfica guardada en:\n{ruta}')
    except Exception as exc:
        sp.popup_error(f'No se pudo guardar la gráfica:\n{exc}')


def redibujar_resultados(window):
    """Tras reconstruir la ventana, vuelve a incrustar la figura si existía."""
    if estado.ultima_figura is not None:
        try:
            _embed_figure(window, estado.ultima_figura)
        except Exception:
            pass


def _dialogo_editar_config():
    """Abre un diálogo para editar el bloque `pso` del config.json del modelo RNA cargado."""
    if estado.ruta_rna is None:
        sp.popup_error('No hay modelo RNA cargado. Cárguelo primero.')
        return None

    ruta_config = Path(estado.ruta_rna) / 'config.json'
    try:
        cfg = json.loads(ruta_config.read_text(encoding='utf-8'))
    except Exception as exc:
        sp.popup_error(f'No se pudo leer config.json:\n{exc}')
        return None

    pso_cfg = cfg.get('pso', {})

    layout = [
        [sp.Text("Editar parámetros PSO del modelo RNA",
                 font=("Arial", 14, "bold"),
                 expand_x=True, justification='center')],
        [sp.Text(f"Archivo: {ruta_config}", font=("Arial", 9))],
        [sp.HSeparator()],

        [sp.Text("Nº Partículas (NP)",         size=(28, 1)),
         sp.Input(key='cfg-NP-',     size=(10, 1),
                  default_text=str(pso_cfg.get('NP', 30)))],
        [sp.Text("Nº Iteraciones (NI)",        size=(28, 1)),
         sp.Input(key='cfg-NI-',     size=(10, 1),
                  default_text=str(pso_cfg.get('NI', 50)))],
        [sp.Text("Optimización (OPT)",         size=(28, 1)),
         sp.Combo(['Minimización', 'Maximización'],
                  key='cfg-OPT-', size=(18, 1), readonly=True,
                  default_value=pso_cfg.get('OPT', 'Minimización'))],
        [sp.Text("Inercia inicial (W_I)",      size=(28, 1)),
         sp.Input(key='cfg-W_I-',    size=(10, 1),
                  default_text=str(pso_cfg.get('W_I', 0.9)))],
        [sp.Text("Inercia final (W_F)",        size=(28, 1)),
         sp.Input(key='cfg-W_F-',    size=(10, 1),
                  default_text=str(pso_cfg.get('W_F', 0.4)))],
        [sp.Text("Coef. cognitivo (C1)",       size=(28, 1)),
         sp.Input(key='cfg-C1-',     size=(10, 1),
                  default_text=str(pso_cfg.get('C1', 1.5)))],
        [sp.Text("Coef. social (C2)",          size=(28, 1)),
         sp.Input(key='cfg-C2-',     size=(10, 1),
                  default_text=str(pso_cfg.get('C2', 1.5)))],
        [sp.Text("Rondas parada temprana",     size=(28, 1)),
         sp.Input(key='cfg-RONDAS-', size=(10, 1),
                  default_text=str(pso_cfg.get('RONDAS', 10)))],
        [sp.Text("Tolerancia parada temprana", size=(28, 1)),
         sp.Input(key='cfg-TOL-',    size=(10, 1),
                  default_text=str(pso_cfg.get('TOL', 1e-6)))],
        [sp.Checkbox("Reducción de inercia (RED_W)",
                     key='cfg-RED_W-',
                     default=bool(pso_cfg.get('RED_W', True)))],
        [sp.Checkbox("Parada temprana (P_T)",
                     key='cfg-P_T-',
                     default=bool(pso_cfg.get('P_T', False)))],

        [sp.HSeparator()],
        [sp.Button('Guardar en config.json',  key='cfg-SAVE-',    size=(22, 1)),
         sp.Button('Aplicar sin guardar',     key='cfg-APPLY-',   size=(20, 1)),
         sp.Button('Cancelar',                key='cfg-CANCEL-',  size=(12, 1))],
    ]

    w = sp.Window('Editar config.json del modelo', layout,
                  modal=True, finalize=True, resizable=False)

    accion = None
    while True:
        ev, vals = w.read()
        if ev in (sp.WIN_CLOSED, 'cfg-CANCEL-'):
            break
        if ev == 'cfg-SAVE-':
            accion = 'save'
            break
        if ev == 'cfg-APPLY-':
            accion = 'apply'
            break
    w.close()

    if accion is None:
        return None

    # --- Validación ---
    try:
        nuevo = {
            'NP':     int(vals['cfg-NP-']),
            'NI':     int(vals['cfg-NI-']),
            'OPT':    vals['cfg-OPT-'],
            'W_I':    float(vals['cfg-W_I-']),
            'W_F':    float(vals['cfg-W_F-']),
            'C1':     float(vals['cfg-C1-']),
            'C2':     float(vals['cfg-C2-']),
            'RONDAS': int(vals['cfg-RONDAS-']),
            'TOL':    float(vals['cfg-TOL-']),
            'RED_W':  bool(vals['cfg-RED_W-']),
            'P_T':    bool(vals['cfg-P_T-']),
        }
        if nuevo['NP'] < 1 or nuevo['NI'] < 1:
            raise ValueError('NP y NI deben ser >= 1.')
        if nuevo['RONDAS'] < 1:
            raise ValueError('RONDAS debe ser >= 1.')
        if nuevo['OPT'] not in ('Minimización', 'Maximización'):
            raise ValueError('OPT debe ser Minimización o Maximización.')
        if nuevo['C1'] < 0 or nuevo['C2'] < 0:
            raise ValueError('C1 y C2 no pueden ser negativos.')
        if nuevo['TOL'] <= 0:
            raise ValueError('TOL debe ser > 0.')
    except (ValueError, TypeError) as exc:
        sp.popup_error(f'Parámetros inválidos:\n{exc}')
        return None

    # --- Reflejar en el formulario del PSO (estado.defaults) ---
    estado.defaults.update({
        'pso-NP-':     str(nuevo['NP']),
        'pso-NI-':     str(nuevo['NI']),
        'pso-OPT-':    nuevo['OPT'],
        'pso-W_I-':    str(nuevo['W_I']),
        'pso-W_F-':    str(nuevo['W_F']),
        'pso-C1-':     str(nuevo['C1']),
        'pso-C2-':     str(nuevo['C2']),
        'pso-RONDAS-': str(nuevo['RONDAS']),
        'pso-TOL-':    str(nuevo['TOL']),
        'pso-RED_W-':  nuevo['RED_W'],
        'pso-P_T-':    nuevo['P_T'],
    })

    # --- Guardar en disco si el usuario lo pidió ---
    if accion == 'save':
        try:
            cfg['pso'] = nuevo
            ruta_config.write_text(
                json.dumps(cfg, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )
            sp.popup_ok(f'config.json actualizado:\n{ruta_config}')
        except Exception as exc:
            sp.popup_error(f'No se pudo guardar config.json:\n{exc}')
            return None

    # Reconstruir la ventana para que el formulario refleje los nuevos valores
    return 'REBUILD'