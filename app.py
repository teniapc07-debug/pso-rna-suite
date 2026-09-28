# app.py
import sys
import PySimpleGUI as sg

from estado import estado, OutputGUI
from ui.ui_pso import layout_pso
from ui.ui_rna import layout_rna
from logica import pso_runner, rna_runner


sg.theme('DarkGrey5')


def _build_window():
    tab_pso = sg.Tab('Optimizador PSO',
                     layout_pso(estado.nv, estado.defaults),
                     key='pso-TAB-', expand_x=True, expand_y=True)
    tab_rna = sg.Tab('Constructor RNA',
                     layout_rna(),
                     key='rna-TAB-', expand_x=True, expand_y=True)

    tabs = sg.TabGroup([[tab_pso, tab_rna]],
                       key='-TABS-', enable_events=True,
                       expand_x=True, expand_y=True)

    w = sg.Window('Suite PSO + RNA', [[tabs]],
                  resizable=True, finalize=True, size=(1400, 900))
    w.maximize()
    return w


def main():
    window = _build_window()

    sys.stdout = OutputGUI(window, 'pso-OUTPUT-', sys.__stdout__)
    sys.stderr = OutputGUI(window, 'pso-OUTPUT-', sys.__stderr__)

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'pso-CERRAR-', 'rna-SALIR-'):
            break

        if event == '-TABS-':
            estado.tab_actual = values['-TABS-']
            continue

        resultado = None
        if isinstance(event, str) and event.startswith('pso-'):
            resultado = pso_runner.handle(event, values, window)
        elif isinstance(event, str) and event.startswith('rna-'):
            resultado = rna_runner.handle(event, values, window)

        if resultado == 'REBUILD':
            window.close()
            window = _build_window()
            sys.stdout = OutputGUI(window, 'pso-OUTPUT-', sys.__stdout__)
            sys.stderr = OutputGUI(window, 'pso-OUTPUT-', sys.__stderr__)

    window.close()


if __name__ == '__main__':
    main()