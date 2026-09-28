# ui/ui_pso.py
import PySimpleGUI as sp


def layout_pso(nv, defaults=None):
    if defaults is None:
        defaults = {}

    metodos = ['Minimización', 'Maximización']
    lst = sp.Combo(
        metodos, font=('Arial', 16), enable_events=True,
        default_value=defaults.get('pso-OPT-', 'Minimización'),
        key='pso-OPT-',
    )

    # --- Selector de modo ---
    modos = [
        [sp.Text('Origen de datos')],
        [
            sp.Radio('Básico', 'MODO-DATOS-PSO',
                     default=defaults.get('pso-MODO_BASICO-', True),
                     key='pso-MODO_BASICO-', enable_events=True),
            sp.Radio('Importar RNA', 'MODO-DATOS-PSO',
                     default=defaults.get('pso-MODO_IMPORTADO-', False),
                     key='pso-MODO_IMPORTADO-', enable_events=True),
        ],
    ]

    # --- Sección 0: Importación de RNA (AHORA CON CONTENIDO) ---
    importacion = [
        [sp.Text('Carpeta con modelo RNA exportado:', font=("Arial", 12))],
        [sp.Input(key='pso-RUTA_RNA-', size=(40, 1), font=("Arial", 12)),
         sp.FolderBrowse('Examinar', size=(10, 1))],
        [sp.Button('Cargar modelo RNA', key='pso-CARGAR_RNA-', size=(20, 1)),
         sp.Button('Quitar modelo',    key='pso-QUITAR_RNA-',  size=(15, 1))],
        [sp.Multiline(size=(60, 5), key='pso-INFO_RNA-', disabled=True,
                      autoscroll=True, font=("Arial", 10),
                      expand_x=True, expand_y=True)],
    ]
    frame_0 = sp.Frame(
        'Importación de RNA', importacion, key='pso-FRAME-0-',
        visible=defaults.get('pso-MODO_IMPORTADO-', False),
        font=("Arial", 12, "bold"),
        size=(600, 200), expand_x=True, expand_y=True,
    )

    # --- Sección 1: Controles (sin la fila de botones) ---
    controles = [
        [sp.Text("Nº Partículas", font=("Arial", 16), size=(13, 1)),
         sp.Input(key='pso-NP-', size=(10, 1), font=("Arial", 16),
                  default_text=defaults.get('pso-NP-', '10'))],
        [sp.Text("Nº Variables", font=("Arial", 16), size=(13, 1)),
         sp.Input(key='pso-NV-', size=(10, 1), font=("Arial", 16),
                  enable_events=True,
                  default_text=str(nv) if nv > 0 else ''),
         sp.Button('Actualizar', size=(10, 1), key='pso-ACTUALIZAR-')],
        [sp.Text("Nº Iteraciones", font=("Arial", 16), size=(13, 1)),
         sp.Input(key='pso-NI-', size=(10, 1), font=("Arial", 16),
                  default_text=defaults.get('pso-NI-', '10'))],
        [sp.Text("Función objetivo", font=("Arial", 16), size=(13, 1)),
         sp.Input(key='pso-FUNCION-', size=(25, 1), font=("Arial", 16),
                  default_text=defaults.get('pso-FUNCION-', '')),
         sp.Button('Ayuda', size=(10, 1), key='pso-AYUDA-')],
        [sp.Text("Optimización", font=("Arial", 16), size=(13, 1)), lst],
        [sp.Checkbox("Reducción de Inercia",
                     default=defaults.get('pso-D_W-', False),
                     key='pso-D_W-', size=(15)),
         sp.Checkbox("Parada temprana",
                     default=defaults.get('pso-P_T-', False),
                     key='pso-P_T-', size=(12)),
         sp.Checkbox("Gráfica de Historial",
                     default=defaults.get('pso-HIST-', False),
                     key='pso-HIST-', size=(15))],
    ]
    frame_1 = sp.Frame(
        'Controles', controles, key='pso-FRAME-1-',
        visible=defaults.get('pso-MODO_BASICO-', True),
        font=("Arial", 12, "bold"),
        size=(600, 225), expand_x=True, expand_y=True,
    )

    # --- Fila de botones de acción (compartida) ---
    botones_accion = [
        sp.Button('Iniciar PSO',         size=(12, 1), key='pso-INI-'),
        sp.Button('Importar Datos',      size=(12, 1), key='pso-IMPORTAR-'),
        sp.Button('Controles Avanzados', size=(15, 1), key='pso-CONTROLES-'),
        sp.Button('Limpiar Datos',       size=(12, 1), key='pso-LIMPIAR-'),
    ]

    # --- Sección 2: Límites de variables ---
    limites_layout = []
    if nv > 0:
        limites_layout.append([sp.Text("Límites de las variables",
                                       font=("Arial", 14, "bold"))])
        for i in range(nv):
            key_min = f'pso-MIN-{i}-'
            key_max = f'pso-MAX-{i}-'
            limites_layout.append([
                sp.Text(f"X_{i+1}", size=(6, 1), font=("Arial", 12)),
                sp.Text("Inf", size=(4, 1), font=("Arial", 12)),
                sp.Input(key=key_min, size=(8, 1), font=("Arial", 12),
                         default_text=defaults.get(key_min, '')),
                sp.Text("Sup", size=(4, 1), font=("Arial", 12)),
                sp.Input(key=key_max, size=(8, 1), font=("Arial", 12),
                         default_text=defaults.get(key_max, '')),
            ])
    col_limites = sp.Column(limites_layout, scrollable=True,
                            vertical_scroll_only=True,
                            size=(600, 500), key='pso-LIMITES-', visible=True)
    frame_2 = sp.Frame('Límites de las variables', [[col_limites]],
                       font=("Arial", 12, "bold"),
                       size=(400, 275), expand_x=True, expand_y=True)

    # --- Sección 3: Canvas de la gráfica ---
    grafica = [[sp.Canvas(key='pso-CANVAS-', background_color='white',
                          expand_x=True, expand_y=True)]]
    frame_3 = sp.Frame('Evolución del Enjambre', grafica,
                       font=("Arial", 12, "bold"),
                       size=(800, 275), expand_x=True, expand_y=True)

    # --- Sección 4: Salida de texto ---
    salida = [[sp.Multiline(size=(60, 6), font=("Arial", 12),
                            key='pso-OUTPUT-', autoscroll=True,
                            disabled=True, expand_x=True, expand_y=True)]]
    frame_4 = sp.Frame('Salida de ejecución', salida,
                       font=("Arial", 12, "bold"),
                       size=(600, 225), expand_x=True, expand_y=True)

    # --- Composición ---
    col_izq = sp.Column([
        [sp.Frame('Origen de Datos', modos, font=("Arial", 12, "bold"),
                  expand_x=True)],
        [sp.pin(frame_0)],
        [sp.pin(frame_1)],
        [sp.Column([botones_accion], expand_x=True)],
        [frame_4],
    ], vertical_alignment='top', expand_x=True, expand_y=True)

    col_der = sp.Column([
        [frame_2],
        [frame_3],
    ], vertical_alignment='top', expand_x=True, expand_y=True)

    botones_inferiores = [
        sp.Button('Exportar Datos', size=(12, 1), key='pso-EXPORTAR-'),
        sp.Button('Cerrar',         size=(10, 1), key='pso-CERRAR-'),
    ]

    return [
        [sp.HorizontalSeparator()],
        [col_izq, sp.VSeparator(), col_der],
        [sp.HSeparator()],
        [sp.Column([botones_inferiores], justification='center', expand_x=True)],
    ]