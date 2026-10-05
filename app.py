# app.py
import sys
import PySimpleGUI as sg
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
from pathlib import Path

from estado import estado, OutputGUI
from ui.ui_pso import layout_pso
from ui.ui_rna import layout_rna
from ui.ui_resultados import layout_resultados
from logica import pso_runner, rna_runner
from logica.logging_config import configurar_logging


sg.theme('DarkGrey5')


def _build_window():
    tab_rna = sg.Tab('Constructor RNA',
                     layout_rna(),
                     key='rna-TAB-', expand_x=True, expand_y=True)
    
    tab_pso = sg.Tab(
        'Optimizador PSO',
        layout_pso(
            estado.nv, estado.defaults,
            rna_info=estado.rna_info_texto, mostrar_editar_config=(estado.ruta_rna is not None), modelo_actual=estado.modelo_combo_actual
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
        event, values = window.read()

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

    window.close()


if __name__ == '__main__':
    main()