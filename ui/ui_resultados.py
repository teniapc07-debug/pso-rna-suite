# ui/ui_resultados.py
import PySimpleGUI as sg


def layout_resultados(historial_visible=False):
    # --- Multiline (izquierda) ---
    salida = [[
        sg.Multiline(
            size=(60, 20), font=("Arial", 12),
            key='res-OUTPUT-', autoscroll=True, disabled=True,
            expand_x=True, expand_y=True,
        )
    ]]
    frame_out = sg.Frame(
        'Salida de ejecución', salida,
        font=("Arial", 12, "bold"),
        expand_x=True, expand_y=True,
    )

    # --- Canvas (derecha) ---
    grafica = [[
        sg.Canvas(
            key='res-CANVAS-', background_color='white',
            expand_x=True, expand_y=True,
        )
    ]]
    frame_graf = sg.Frame(
        'Evolución del Enjambre', grafica,
        font=("Arial", 12, "bold"),
        expand_x=True, expand_y=True,
    )

    col_izq = sg.Column(
        [[frame_out]],
        expand_x=True, expand_y=True, vertical_alignment='top',
    )
    col_der = sg.Column(
        [[frame_graf]],
        expand_x=True, expand_y=True, vertical_alignment='top',
    )

    # --- Tabla de historial (colapsable) ---
    tabla_layout = [
        [sg.Table(
            values=[],
            headings=['#', 'Origen', 'NP', 'NI', 'Mejor valor', 'Tiempo', 'Fecha'],
            key='res-HISTORIAL-',
            col_widths=[5, 25, 6, 6, 14, 10, 20],
            auto_size_columns=False,
            justification='left',
            num_rows=8,
            alternating_row_color='#2A2A2A',
            enable_events=True,
            expand_x=True,
        )],
        [sg.Column(
            [[
                sg.Button('Limpiar historial', key='res-HIST-LIMPIAR-', size=(18, 1)),
                sg.Button('Exportar a CSV',    key='res-HIST-EXPORTAR-', size=(18, 1)),
            ]],
            expand_x=True,
            pad=((0, 0), (8, 4)),     # ← espacio arriba y abajo de los botones
        )],
    ]
    frame_hist = sg.Frame(
        'Historial de ejecuciones (doble clic para restaurar parámetros)',
        tabla_layout, font=("Arial", 12, "bold"),
        expand_x=True, expand_y=False,
    )
    contenedor_hist = sg.Column(
        [[frame_hist]],
        key='res-HIST-CONT-',
        visible=historial_visible,
        expand_x=True,
    )

    return [
        [sg.HorizontalSeparator()],
        [col_izq, sg.VSeparator(), col_der],
        [sg.HorizontalSeparator()],
        [sg.Column([[
            sg.Button('Mostrar/Ocultar historial', key='res-HIST-TOGGLE-',
                      size=(25, 1)),
            sg.Button('Guardar gráfica (PNG)', key='res-GUARDAR_PNG-',
                      size=(20, 1)),
            sg.Button('Limpiar salida', key='res-LIMPIAR-', size=(15, 1)),
        ]], justification='center', expand_x=True)],
        [contenedor_hist],
    ]