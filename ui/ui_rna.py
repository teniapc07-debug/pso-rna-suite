# ui/ui_rna.py
import FreeSimpleGUI as sg


def layout_rna():
    control = [
        [sg.Text('Numero de muestras de entrenamiento'),
         sg.Input(key='rna-MUESTRAS-', size=(10, 1))],
        [sg.Text('Numero de capas ocultas'),
         sg.Input(key='rna-CAPAS-', size=(10, 1))],
        [sg.Text('Numero de neuronas por capa (separadas por comas)'),
         sg.Input(key='rna-NEURONAS-', size=(30, 1))],
        [sg.Text('Funcion de activacion (relu, sigmoid, tanh)'),
         sg.Input(key='rna-ACTIVACION-', size=(10, 1))],
        [sg.Text('Numero de epocas'),
         sg.Input(key='rna-EPOCAS-', size=(10, 1))],
        [sg.Text('Tamaño del batch'),
         sg.Input(key='rna-BATCH-', size=(10, 1))],
    ]
    frame1 = sg.Frame('Controles de la RNA', control, font='Any 12', expand_x=True)

    grafica = [[sg.Canvas(key='rna-CANVAS-', size=(500, 350),
                          expand_x=True, expand_y=True)]]
    frame2 = sg.Frame('Grafica de la RNA', grafica, font='Any 12', expand_x=True)

    validación = [
        [sg.Text('Predicciones del modelo', font='Any 12', expand_x=True)],
        [sg.Text('Ingrese los valores de las variables (separados por comas)'),
         sg.Input(key='rna-VALORES-', size=(30, 1))],
        [sg.Button('Predecir', key='rna-PREDICIR-', size=(15, 1))],
    ]
    frame3 = sg.Frame('Validación de entradas', validación,
                      font='Any 12', expand_x=True)

    funcion = [
        [sg.Text('Funcion matematica (ejemplo: x1**2 + x2**2)'),
         sg.Input(key='rna-FUNCION-', size=(30, 1))],
        [sg.Text('Numero de variables'),
         sg.Input(key='rna-NV-', size=(10, 1))],
        [sg.Text('Limite inferior por variable (separados por comas)'),
         sg.Input(key='rna-LIM_INF-', size=(30, 1))],
        [sg.Text('Limite superior por variable (separados por comas)'),
         sg.Input(key='rna-LIM_SUP-', size=(30, 1))],
    ]
    frame0 = sg.Frame('Datos Sinteticos', funcion, key='rna-FRAME-0-',
                      font='Any 12', expand_x=True)

    importacion = [
        [sg.Text('Columna objetivo (y) en el CSV')],
        [sg.Combo(values=[], key='rna-COL_Y-', size=(20, 1),
                  readonly=True, enable_events=True)],
        [sg.Button('Importar Datos', key='rna-IMPORTAR-', size=(15, 1))],
    ]
    frame4 = sg.Frame('Datos Importados', importacion, key='rna-FRAME-4-',
                      visible=False, font='Any 12', expand_x=True)

    selector_modo = [
        [sg.Text('Modo de datos')],
        [
            sg.Radio('Sintéticos', 'MODO-DATOS-RNA',
                     key='rna-MODO-SINTETICO-', default=True, enable_events=True),
            sg.Radio('Importados', 'MODO-DATOS-RNA',
                     key='rna-MODO-IMPORTADO-', enable_events=True),
        ],
    ]

    columna1 = [
        [sg.Frame('Origen de datos', selector_modo, expand_x=True)],
        [sg.pin(frame0)],
        [sg.pin(frame4)],
        [sg.HorizontalSeparator()],
        [frame1],
        [sg.Button('Generar RNA', key='rna-GENERAR-', size=(15, 1))],
    ]

    return [
        [sg.Column(columna1, vertical_alignment='top'),
         sg.VerticalSeparator(), frame2],
        [sg.HorizontalSeparator()],
        [sg.Text('Progreso del entrenamiento:'),
         sg.ProgressBar(1, orientation='h', size=(40, 20),
                        key='rna-PROGRESO-', expand_x=True),
         sg.Text('0%', key='rna-PORCENTAJE-', size=(6, 1))],
        [sg.Text('Esperando parámetros...', key='rna-ESTADO-', expand_x=True)],
        [sg.HorizontalSeparator()],
        [frame3],
        [sg.HorizontalSeparator()],
        [sg.Button('Exportar Modelo', key='rna-EXPORTAR-', size=(15, 1)),
         sg.Button('Salir', key='rna-SALIR-', size=(10, 1))],
    ]