# ui/ui_resultados.py
import PySimpleGUI as sp


def layout_resultados():
    # --- Multiline (izquierda) ---
    salida = [[
        sp.Multiline(
            size=(50, 20), font=("Arial", 12),
            key='res-OUTPUT-', autoscroll=True, disabled=True,
            expand_x=True, expand_y=True,
        )
    ]]
    frame_out = sp.Frame(
        'Salida de ejecución', salida,
        font=("Arial", 12, "bold"),
        expand_x=True, expand_y=True,
    )

    # --- Canvas (derecha) ---
    grafica = [[
        sp.Canvas(
            key='res-CANVAS-', background_color='white',
            expand_x=True, expand_y=True,
        )
    ]]
    frame_graf = sp.Frame(
        'Evolución del Enjambre', grafica,
        font=("Arial", 12, "bold"),
        expand_x=True, expand_y=True,
    )

    # --- Composición en dos columnas ---
    col_izq = sp.Column(
        [[frame_out]],
        expand_x=True, expand_y=True, vertical_alignment='top',
    )
    col_der = sp.Column(
        [[frame_graf]],
        expand_x=True, expand_y=True, vertical_alignment='top',
    )

    return [
        [sp.HorizontalSeparator()],
        [col_izq, sp.VSeparator(), col_der],
        [sp.HorizontalSeparator()],
        [sp.Column([[
            sp.Button('Guardar gráfica (PNG)', key='res-GUARDAR_PNG-', size=(20, 1)),
            sp.Button('Limpiar salida',        key='res-LIMPIAR-',      size=(15, 1)),
        ]], justification='center', expand_x=True)],
    ]