# logica/pso_runner.py
import sys
from pathlib import Path
from estado import estado, OutputGUI
import json
import numpy as np
import pandas as pd
import PySimpleGUI as sp
import matplotlib.pyplot as plt
import logging
from logica.logging_config import operacion_log
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from logica import historial
from logica import io_tablas

from logica import buscador_modelos
from PSO_MV import Enjambre_M
from PSO_MV import funcion_objetivo as modulo_funcion_objetivo
from RNA import Hibrido
from estado import estado

logger = logging.getLogger(__name__)

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
    if event == 'pso-REENTRENAR-':
        return _preparar_reentrenamiento(window)
    
    if event == 'res-HISTTOGGLE-':
        toggle_historial(window)
        return None

    if event == 'res-HISTLIMPIAR-':
        limpiar_historial_ui(window)
        return None
    
    if event == 'res-LIMPIAR-':
        window['res-OUTPUT-'].update('')
        return None

    if event == 'res-GUARDAR_PNG-':
        guardar_grafica_png(window)
        return None

    if event == 'res-HISTEXPORTAR-':
        exportar_historial_tabla()
        return None

    if event == 'res-HISTTABLA-':
        seleccion = values.get('res-HISTTABLA-', [])
        if seleccion:
            return restaurar_desde_historial(window, seleccion[0])
        return None

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
        # Prioridad: ComboBox > campo oculto de FolderBrowse
        valor_combo = values.get('pso-MODELO_COMBO-', '').strip()
        estado.modelo_combo_actual = valor_combo
        valor_manual = values.get('pso-RUTA_RNA-', '').strip()
        ruta = buscador_modelos.resolver_ruta(
            valor_combo or valor_manual,
            estado.modelos_disponibles,
        )
        if not ruta:
            sp.popup_error('Seleccione un modelo del combo o una carpeta '
                           'con "Examinar…".')
            return None
        try:
            f_pred, nv_rna, lim_inf, lim_sup, origen = \
                Hibrido.cargar_funcion_prediccion(ruta)
        except Exception as exc:
            sp.popup_error(f'Error al cargar el modelo RNA:\n{exc}')
            return None

        logger.info(f"Modelo RNA cargado: {ruta}")
        estado.modelo_con_origen = origen

        estado.funcion_objetivo_rna = f_pred
        estado.ruta_rna = ruta
        estado.nv = int(nv_rna)
        for i in range(nv_rna):
            estado.defaults[f'pso-MIN-{i}-'] = str(lim_inf[i])
            estado.defaults[f'pso-MAX-{i}-'] = str(lim_sup[i])

        # Rellenar parámetros PSO sugeridos (si config.json los tiene)
        try:
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

        # --- Advertencia si el modelo tiene función simbólica de origen ---
        aviso_conflicto = ''
        if origen and origen.get('modo') == 'sintetico' and origen.get('funcion'):
            funcion_origen = origen['funcion']
            funcion_actual = values.get('pso-FUNCION-', '').strip()
            if funcion_actual and funcion_actual != funcion_origen:
                # Popup de decisión: reemplazar la función simbólica actual
                reemplazar = sp.popup_yes_no(
                    f'Este modelo fue entrenado con la función:\n\n'
                    f'    {funcion_origen}\n\n'
                    f'Tu campo "Función objetivo" tiene otra expresión:\n\n'
                    f'    {funcion_actual}\n\n'
                    f'¿Reemplazarla por la del modelo?',
                    title='Conflicto de función objetivo',
                )
                if reemplazar == 'Yes':
                    estado.defaults['pso-FUNCION-'] = funcion_origen
                    aviso_conflicto = '(función simbólica reemplazada por la del modelo)'
                else:
                    aviso_conflicto = '(función simbólica conservada)'
            elif not funcion_actual:
                # Rellenar automáticamente sin preguntar
                estado.defaults['pso-FUNCION-'] = funcion_origen

        texto_info = (
            f'Modelo cargado desde: {ruta}\n'
            f'nv={nv_rna}  |  lim_inf={lim_inf}\n'
            f'lim_sup={lim_sup}\n'
            f'Se usará el modelo RNA como función objetivo. {aviso_conflicto}'
        )
        estado.rna_info_texto = texto_info
        window['pso-INFO_RNA-'].update(texto_info)

        # Mostrar botón "Editar config"
        window['pso-PIN_EDITAR-'].update(visible=True)

        # Mostrar botón "Reentrenar" solo si hay origen
        window['pso-PIN_REENTRENAR-'].update(visible=origen is not None)

        window['pso-ESTADO-'].update('Modelo RNA listo. Pulsa "Iniciar PSO".')
        window['pso-PROGRESO-'].update(current_count=0, max=1)
        window['pso-PORCENTAJE-'].update('0%')
        return 'REBUILD'

    # --- Quitar modelo RNA ---
    if event == 'pso-QUITAR_RNA-':
        estado.funcion_objetivo_rna = None
        estado.ruta_rna = None
        estado.modelo_con_origen = None
        texto = 'No hay modelo RNA cargado. Se usará la función simbólica.'
        estado.rna_info_texto = texto
        window['pso-INFO_RNA-'].update(texto)
        window['pso-PIN_EDITAR-'].update(visible=False)
        window['pso-PIN_REENTRENAR-'].update(visible=False)
        logger.info("Modelo RNA descargado")
        return None

    # --- Importar CSV de parámetros ---
    if event == 'pso-IMPORTAR-':
        _importar_csv_params()
        return 'REBUILD'

    # --- Exportar CSV de parámetros ---
    if event == 'pso-EXPORTAR-':
        _exportar_csv_params(values)
        return None

    # --- Limpiar datos ---
    if event == 'pso-LIMPIAR-':
        logger.info("Estado reseteado")
        _limpiar()
        return 'REBUILD'

    # --- Iniciar PSO ---
    if event == 'pso-INI-':
        _ejecutar_pso(values, window)
        return None

    # --- Refrescar lista de modelos ---
    if event == 'pso-REFRESCAR_LISTA-':
        refrescar_lista_modelos(window)
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
    archivo = sp.popup_get_file(
        'Seleccione un archivo de parámetros',
        file_types=io_tablas.filtros_lectura(),
        no_window=True,
    )
    if not archivo:
        return
    try:
        df = io_tablas.leer_tabla(archivo, dtype=str)
        if not {'parametro', 'valor'}.issubset(df.columns):
            raise ValueError("El archivo debe tener columnas 'parametro' y 'valor'.")
        p = dict(zip(df['parametro'].astype(str).str.strip(),
                     df['valor'].fillna('').astype(str).str.strip()))

        # --- Helpers tolerantes a campos vacíos ---
        def _num(nombre, cast=int):
            v = p.get(nombre, '')
            if v == '':
                return None
            return cast(v)

        def _bool(nombre):
            v = p.get(nombre, '').lower()
            if v == '':
                return None
            if v not in {'true', 'false'}:
                raise ValueError(f'{nombre} debe ser True/False')
            return v == 'true'

        # --- NV es obligatorio ---
        nv = _num('NV', int)
        if nv is None:
            raise ValueError("El archivo no contiene el campo obligatorio 'NV'.")
        if nv < 1:
            raise ValueError('NV debe ser >= 1.')

        estado.nv = nv
        updates = {'pso-NV-': str(nv)}

        val = _num('NP', int)
        if val is not None:
            updates['pso-NP-'] = str(val)
        val = _num('NI', int)
        if val is not None:
            updates['pso-NI-'] = str(val)

        if 'FUNCION' in p:
            updates['pso-FUNCION-'] = p['FUNCION']
        if p.get('OPT', ''):
            updates['pso-OPT-'] = p['OPT']

        for flag, clave in (('D_W', 'pso-D_W-'),
                            ('P_T', 'pso-P_T-'),
                            ('HIST', 'pso-HIST-')):
            val = _bool(flag)
            if val is not None:
                updates[clave] = val

        for i in range(nv):
            v = p.get(f'MIN_{i}', '')
            if v != '':
                updates[f'pso-MIN-{i}-'] = str(float(v))
            v = p.get(f'MAX_{i}', '')
            if v != '':
                updates[f'pso-MAX-{i}-'] = str(float(v))

        estado.defaults.update(updates)
        logger.info(f"Parámetros importados de {archivo}")
    except Exception as exc:
        logger.error(f"Error al importar parámetros: {exc}")
        sp.popup_error(f'Error al importar:\n{exc}')

def _exportar_csv_params(values):
    _guardar_defaults(values)
    archivo = sp.popup_get_file(
        'Guardar archivo de parámetros',
        save_as=True,
        file_types=io_tablas.filtros_escritura(),
        no_window=True,
        default_extension='.xlsx',
    )
    if not archivo:
        return
    carpeta = Path('resultados_pso')
    carpeta.mkdir(exist_ok=True)
    destino = Path(archivo)
    if destino.parent == Path('.'):
        destino = carpeta / destino.name

    mapa = {
        'NP':      'pso-NP-',
        'NI':      'pso-NI-',
        'FUNCION': 'pso-FUNCION-',
        'OPT':     'pso-OPT-',
        'D_W':     'pso-D_W-',
        'P_T':     'pso-P_T-',
        'HIST':    'pso-HIST-',
    }
    nv = estado.nv

    filas = [('NV', nv)]
    for nombre, clave in mapa.items():
        filas.append((nombre, estado.defaults.get(clave, '')))
    for i in range(nv):
        filas.append((f'MIN_{i}', estado.defaults.get(f'pso-MIN-{i}-', '')))
        filas.append((f'MAX_{i}', estado.defaults.get(f'pso-MAX-{i}-', '')))

    df = pd.DataFrame(filas, columns=['parametro', 'valor'])

    try:
        ruta = io_tablas.escribir_tabla(df, destino, hoja='Parametros')
        logger.info(f"Parámetros exportados a {ruta}")
        sp.popup_ok(f'Datos exportados a {ruta}')
    except Exception as exc:
        logger.error(f"Error al exportar: {exc}")
        sp.popup_error(f'Error al exportar:\n{exc}')

def _limpiar():
    estado.nv = 0
    estado.funcion_objetivo_rna = None
    estado.ruta_rna = None
    estado.rna_info_texto = 'No hay modelo RNA cargado. Se usará la función simbólica.'
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
        logger.error(f"Error de validación en PSO: {exc}")
        return

    optimizacion = values['pso-OPT-']
    parada_temprana = bool(estado.defaults.get('pso-P_T-', values['pso-P_T-']))

    # --- Preparar UI de progreso ---
    with operacion_log('pso') as ruta_log:
        logger.info(
            f"Configuración PSO: NP={n_particulas}, NI={n_iteraciones}, "
            f"NV={nv_local}, OPT={optimizacion}"
        )
        logger.info(f"Origen función objetivo: {origen}")
        logger.info(f"Límites: inf={lim_inf}, sup={lim_sup}")
        logger.info(f"Controles: w_i={w_i}, w_f={w_f}, c1={c1}, c2={c2}, "
                    f"parada_temprana={parada_temprana}")

        window['pso-PROGRESO-'].update(current_count=0, max=n_iteraciones)
        window['pso-PORCENTAJE-'].update('0%')
        window['pso-ESTADO-'].update(f'Iniciando PSO ({origen}) ...')
        window.refresh()

        def _on_iteracion(actual, total, mejor_valor):
            logger.debug(f"Iteración {actual}/{total}, mejor={float(mejor_valor):.6g}")
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
                iteracion_callback=_on_iteracion,
            )
        except ValueError as exc:
            logger.error(f"Partícula fuera de dominio: {exc}")
            sp.popup_error(f"Una partícula salió del dominio:\n{exc}")
            window['pso-ESTADO-'].update('Error durante la ejecución.')
            return

        try:
            mejor = float(enj.valor_optimo)
            logger.info(f"PSO completado: iter={enj.iteracion_optimo}, mejor={mejor:.6g}")
            window['pso-ESTADO-'].update(
                f'Completado ({enj.iteracion_optimo} iters) — mejor valor: {mejor:.6g}')
            window['pso-PROGRESO-'].update(current_count=enj.iteracion_optimo,
                                           max=enj.iteracion_optimo)
            window['pso-PORCENTAJE-'].update('100%')
        except Exception:
            pass

                # --- Registrar en el historial ---
        try:
            origen = (Path(estado.ruta_rna).name
                      if estado.ruta_rna
                      else (values['pso-FUNCION-'].strip() or '—'))
            entrada = {
                'origen': origen,
                'nv': nv_local,
                'np': n_particulas,
                'ni': n_iteraciones,
                'opt': optimizacion,
                'w_i': w_i, 'w_f': w_f, 'c1': c1, 'c2': c2,
                'reduccion_w': reduccion_w,
                'parada_temprana': parada_temprana,
                'mejor_valor': float(enj.valor_optimo),
                'mejor_posicion': [
                    float(x) for x in np.asarray(enj.posicion_optima).ravel()
                ],
                'iteracion_optimo': int(enj.iteracion_optimo),
                'tiempo_seg': float(getattr(enj, 'tiempo_total', 0.0)),
            }
            entrada_guardada = historial.agregar_entrada(entrada)
            logger.info(f"Historial: entrada id={entrada_guardada['id']} "
                        f"({origen}, mejor={entrada['mejor_valor']:.6g})")
            if estado.historial_visible:
                refrescar_tabla_historial(window)
        except Exception as exc:
            logger.error(f"No se pudo registrar la ejecución: {exc}")

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
            logger.info(f"Config.json actualizado: {ruta_config}")
            sp.popup_ok(f'config.json actualizado:\n{ruta_config}')
        except Exception as exc:
            logger.error(f"Error al guardar config.json: {exc}")
            sp.popup_error(f'No se pudo guardar config.json:\n{exc}')
            return None

    # Reconstruir la ventana para que el formulario refleje los nuevos valores
    logger.info(f"Config editado: {nuevo}")
    return 'REBUILD'

# ---------------------------------------------------------------
# Historial
# ---------------------------------------------------------------
def _formato_tiempo(seg):
    if seg < 60:
        return f"{seg:.2f}s"
    m = int(seg // 60)
    s = seg % 60
    return f"{m}m {s:.0f}s"


def refrescar_tabla_historial(window):
    """Vuelca las últimas 20 entradas (más recientes primero) en la tabla."""
    entradas = historial.cargar_historial()
    ultimas = list(reversed(entradas[-20:]))
    filas = []
    for e in ultimas:
        origen = str(e.get('origen', '—'))
        if len(origen) > 25:
            origen = origen[:22] + '...'
        filas.append([
            e.get('id', '?'),
            origen,
            e.get('np', '?'),
            e.get('ni', '?'),
            f"{e.get('mejor_valor', 0):.6g}",
            _formato_tiempo(float(e.get('tiempo_seg', 0.0))),
            str(e.get('timestamp', '')).replace('T', ' ')[:19],
        ])
    window['res-HISTTABLA-'].update(values=filas)


def toggle_historial(window):
    """Alterna la visibilidad del panel y refresca la tabla al mostrarlo."""
    estado.historial_visible = not estado.historial_visible
    window['res-HISTCONT-'].update(visible=estado.historial_visible)
    if estado.historial_visible:
        refrescar_tabla_historial(window)


def limpiar_historial_ui(window):
    """Vacía el historial tras confirmación del usuario."""
    if not sp.popup_yes_no('¿Vaciar todo el historial de ejecuciones?'):
        return
    historial.limpiar_historial()
    window['res-HISTTABLA-'].update(values=[])
    sp.popup_ok('Historial vaciado.')


def exportar_historial_tabla():
    """Exporta el historial completo a Excel (o CSV si el usuario lo pide)."""
    entradas = historial.cargar_historial()
    if not entradas:
        sp.popup_error('No hay historial para exportar.')
        return
    archivo = sp.popup_get_file(
        'Guardar historial',
        save_as=True,
        file_types=io_tablas.filtros_escritura(),
        no_window=True,
        default_extension='.xlsx',
    )
    if not archivo:
        return
    destino = Path(archivo)

    filas = []
    for e in entradas:
        filas.append({
            'id': e.get('id', ''),
            'timestamp': e.get('timestamp', ''),
            'origen': e.get('origen', ''),
            'np': e.get('np', ''),
            'ni': e.get('ni', ''),
            'opt': e.get('opt', ''),
            'mejor_valor': e.get('mejor_valor', ''),
            'iteracion_optimo': e.get('iteracion_optimo', ''),
            'tiempo_seg': e.get('tiempo_seg', ''),
        })
    df = pd.DataFrame(filas)

    try:
        ruta = io_tablas.escribir_tabla(df, destino, hoja='Historial')
        logger.info(f"Historial exportado a {ruta}")
        sp.popup_ok(f'Historial exportado a:\n{ruta}')
    except Exception as exc:
        logger.error(f"Error al exportar historial: {exc}")
        sp.popup_error(f'Error al exportar:\n{exc}')


def restaurar_desde_historial(window, idx_fila):
    """Restaura los parámetros de la fila seleccionada en el tab PSO.

    ``idx_fila`` es el índice sobre las filas mostradas (0 = más reciente).
    Devuelve ``'REBUILD'`` si la restauración fue exitosa.
    """
    entradas = historial.cargar_historial()
    ultimas = list(reversed(entradas[-20:]))
    if not (0 <= idx_fila < len(ultimas)):
        return None
    e = ultimas[idx_fila]

    estado.defaults.update({
        'pso-NP-':     str(e.get('np', '')),
        'pso-NI-':     str(e.get('ni', '')),
        'pso-OPT-':    e.get('opt', 'Minimización'),
        'pso-W_I-':    str(e.get('w_i', 0.9)),
        'pso-W_F-':    str(e.get('w_f', 0.4)),
        'pso-C1-':     str(e.get('c1', 1.5)),
        'pso-C2-':     str(e.get('c2', 1.5)),
        'pso-D_W-':    bool(e.get('reduccion_w', True)),
        'pso-P_T-':    bool(e.get('parada_temprana', False)),
    })
    estado.nv = int(e.get('nv', estado.nv))

    # Restaurar el origen de la función objetivo
    origen = str(e.get('origen', ''))
    if estado.ruta_rna and Path(estado.ruta_rna).name == origen:
        # El modelo cargado coincide con el registrado: nada que hacer
        pass
    elif origen and origen != '—':
        # Es una función simbólica (o un modelo que ya no está cargado)
        if not estado.ruta_rna:
            estado.defaults['pso-FUNCION-'] = origen

    logger.info(f"Parámetros restaurados desde historial id={e.get('id')}")
    sp.popup_ok(f"Parámetros restaurados desde la ejecución #{e.get('id')}.")
    return 'REBUILD'

# ---------------------------------------------------------------
# Lista de modelos RNA
# ---------------------------------------------------------------
def refrescar_lista_modelos(window):
    """Reescanea el filesystem y vuelve a poblar el ComboBox."""
    modelos = buscador_modelos.buscar_modelos_disponibles()
    estado.modelos_disponibles = modelos
    displays = [m['display'] for m in modelos]

    # Mantener la selección actual si sigue existiendo
    actual = estado.defaults.get('pso-MODELO_COMBO-', '')
    try:
        actual = window['pso-MODELO_COMBO-'].get()
    except Exception:
        pass

    window['pso-MODELO_COMBO-'].update(values=displays)
    if actual in displays:
        window['pso-MODELO_COMBO-'].update(value=actual)

    if not displays:
        window['pso-INFO_RNA-'].update(
            'No se encontraron modelos RNA en el proyecto.\n'
            'Exporta un modelo desde el tab RNA o usa "Examinar…".'
        )
    return modelos

# ---------------------------------------------------------------
# Preparar reentrenamiento
# ---------------------------------------------------------------
def _preparar_reentrenamiento(window):
    """Prepara el handoff PSO → RNA.

    Guarda los metadatos del modelo cargado en `estado.rna_presets` y
    solicita a `app.py` que reconstruya la ventana y cambie al tab RNA.
    """
    origen = estado.modelo_con_origen
    if not origen:
        sp.popup_error(
            'Este modelo no tiene metadatos de entrenamiento.\n\n'
            'No es posible reentrenar automáticamente. Carga el archivo '
            'de datos y rellena los parámetros manualmente.'
        )
        return None

    # Guardar presets a partir de los metadatos del origen
    estado.rna_presets = {
        'modo':       origen.get('modo', 'sintetico'),
        'funcion':    origen.get('funcion'),
        'nv':         origen.get('nv'),
        'lim_inf':    origen.get('lim_inf') or [],
        'lim_sup':    origen.get('lim_sup') or [],
        'columnas_x': origen.get('columnas_x') or [],
        'muestras':   origen.get('muestras'),
        'capas':      origen.get('capas'),
        'neuronas':   origen.get('neuronas') or [],
        'activacion': origen.get('activacion'),
        'epocas':     origen.get('epocas'),
        'batch':      origen.get('batch'),
    }
    logger.info(f"Reentrenamiento preparado (origen={estado.ruta_rna})")
    return 'IR_A_RNA'