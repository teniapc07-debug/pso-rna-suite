# app.py
import sys
import os
import tkinter.messagebox as _mb
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['ABSL_LOGGING_VERBOSITY'] = '3'
from pathlib import Path
import FreeSimpleGUI as sg

from estado import estado, OutputGUI
from ui.ui_pso import layout_pso
from ui.ui_rna import layout_rna
from ui.ui_resultados import layout_resultados
from logica import pso_runner, rna_runner
from logica.logging_config import configurar_logging

try:
    import tensorflow  # noqa: F401
except ImportError as _exc:
    _msg = str(_exc)
    if 'msvcp140' in _msg or 'DLL' in _msg or 'vcruntime' in _msg:
        _mb.showerror(
            "Componente del sistema faltante",
            "Falta el Microsoft Visual C++ Redistributable.\n\n"
            "TensorFlow lo necesita para funcionar.\n\n"
            "Descárgalo e instálalo desde:\n"
            "https://aka.ms/vc14/vc_redist.x64.exe\n\n"
            "Después de instalarlo, reinicia la aplicación."
        )
        sys.exit(1)
    else:
        # Otro error de import distinto: relanzarlo
        raise


sg.theme('DarkGrey5')


def _build_window():
    tab_rna = sg.Tab('Constructor RNA',
                     layout_rna(),
                     key='rna-TAB-', expand_x=True, expand_y=True)
    
    tab_pso = sg.Tab(
        'Optimizador PSO',
        layout_pso(
            estado.nv, estado.defaults,
            rna_info=estado.rna_info_texto, mostrar_editar_config=(estado.ruta_rna is not None), modelo_actual=estado.modelo_combo_actual, mostrar_reentrenar=(estado.modelo_con_origen is not None),
        ),
        key='pso-TAB-', expand_x=True, expand_y=True,
    )

    tab_res = sg.Tab('Resultados',
                     layout_resultados(estado.historial_visible),
                     key='res-TAB-', expand_x=True, expand_y=True)

    tabs = sg.TabGroup([[tab_pso, tab_rna, tab_res]],
                       key='-TABS-', enable_events=True,
                       expand_x=True, expand_y=True)

    w = sg.Window('Suite PSO + RNA', [[tabs]],
                  resizable=True, finalize=True, size=(1400, 900))
    w.maximize()
    return w


def main():
    window = _build_window()

    configurar_logging(window, 'res-OUTPUT-')
    pso_runner.refrescar_lista_modelos(window)

    sys.stdout = OutputGUI(window, 'res-OUTPUT-', sys.__stdout__)
    sys.stderr = OutputGUI(window, 'res-OUTPUT-', sys.__stderr__)

    while True:
        result = window.read()
        if result is None:
            break
        event, values = result

        if event in (sg.WIN_CLOSED, 'pso-CERRAR-', 'rna-SALIR-'):
            break

        if event == '-TABS-':
            estado.tab_actual = values['-TABS-']
            # Si el usuario acaba de volver al tab PSO y hay una exportación nueva,
            # refrescar la lista y seleccionar el modelo recién exportado.
            if estado.tab_actual == 'pso-TAB-' and estado.ultima_exportacion:
                pso_runner.refrescar_lista_modelos(window)
                try:
                    nuevo_nombre = Path(estado.ultima_exportacion).name
                    for modelo in estado.modelos_disponibles:
                        if modelo['nombre'] == nuevo_nombre:
                            window['pso-MODELO_COMBO-'].update(value=modelo['display'])
                            break
                except Exception:
                    pass
                estado.ultima_exportacion = None
            continue

        resultado = None
        if isinstance(event, str):
            if event.startswith('pso-') or event.startswith('res-'):
                resultado = pso_runner.handle(event, values, window)
            elif event.startswith('rna-'):
                resultado = rna_runner.handle(event, values, window)

        if resultado == 'REBUILD':
            window.close()
            window = _build_window()
            sys.stdout = OutputGUI(window, 'res-OUTPUT-', sys.__stdout__)
            sys.stderr = OutputGUI(window, 'res-OUTPUT-', sys.__stderr__)
            configurar_logging(window, 'res-OUTPUT-')
            pso_runner.redibujar_resultados(window)
            if estado.historial_visible:
                pso_runner.refrescar_tabla_historial(window)

        elif resultado == 'IR_A_RNA':
            # Reconstruir la ventana y cambiar al tab RNA
            window.close()
            window = _build_window()
            sys.stdout = OutputGUI(window, 'res-OUTPUT-', sys.__stdout__)
            sys.stderr = OutputGUI(window, 'res-OUTPUT-', sys.__stderr__)
            configurar_logging(window, 'res-OUTPUT-')
            pso_runner.redibujar_resultados(window)
            if estado.historial_visible:
                pso_runner.refrescar_tabla_historial(window)
            try:
                window['-TABS-'].Widget.select(1)
            except Exception as exc:
                print(f"[ERROR] No se pudo cambiar de tab: {exc}")
            rna_runner.aplicar_presets(window)

    window.close()


if __name__ == '__main__':
    main()