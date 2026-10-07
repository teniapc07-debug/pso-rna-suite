# ui/ui_resultados.py
import FreeSimpleGUI as sg


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

    # --- Tabla del historial ---
    tabla = sg.Table(
        values=[],
        headings=['#', 'Origen', 'NP', 'NI', 'Mejor valor', 'Tiempo', 'Fecha'],
        key='res-HISTTABLA-',
        col_widths=[5, 25, 6, 6, 14, 10, 20],
        auto_size_columns=False,
        justification='left',
        num_rows=8,
        alternating_row_color='#2A2A2A',
        enable_events=True,
        expand_x=True,
    )

    botones_hist = [
        sg.Button('Limpiar historial', key='res-HISTLIMPIAR-', size=(18, 1)),
        sg.Button('Exportar Historial',    key='res-HISTEXPORTAR-', size=(18, 1)),
    ]

    frame_hist = sg.Frame(
        'Historial de ejecuciones (doble clic para restaurar parámetros)',
        [
            [tabla],
            [sg.Column([botones_hist], expand_x=True, pad=((0, 0), (10, 6)))],
        ],
        font=("Arial", 12, "bold"),
        expand_x=True,
        pad=((0, 0), (5, 5)),
    )

    contenedor_hist = sg.Column(
        [[frame_hist]],
        key='res-HISTCONT-',
        visible=historial_visible,
        expand_x=True,
        pad=((5, 5), (5, 8)),
    )

    return [
        [sg.HorizontalSeparator()],
        [col_izq, sg.VSeparator(), col_der],
        [sg.HorizontalSeparator()],
        [sg.Column([[
            sg.Button('Mostrar/Ocultar historial', key='res-HISTTOGGLE-',
                      size=(25, 1)),
            sg.Button('Guardar gráfica (PNG)', key='res-GUARDAR_PNG-',
                      size=(20, 1)),
            sg.Button('Limpiar salida', key='res-LIMPIAR-', size=(15, 1)),
        ]], justification='center', expand_x=True)],
        [contenedor_hist],
    ]