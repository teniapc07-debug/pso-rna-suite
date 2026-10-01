# ui/ui_pso.py
import PySimpleGUI as sp


def layout_pso(nv, defaults=None, rna_info=None, mostrar_editar_config=False):
    if defaults is None:
        defaults = {}
    if rna_info is None:
        rna_info = 'No hay modelo RNA cargado. Se usará la función simbólica.'

    metodos = ['Minimización', 'Maximización']
    lst = sp.Combo(
        metodos, font=('Arial', 16), enable_events=True,
        default_value=defaults.get('pso-OPT-', 'Minimización'),
        key='pso-OPT-',
    )

    # ------------------------------------------------------------------
    # Sección 0: Importación de RNA (opcional, siempre visible)
    # ------------------------------------------------------------------
    importacion = [
        [sp.Text(
            'Opcional. Si carga un modelo RNA, se ignorará la función simbólica '
            'definida en Controles.',
            font=("Arial", 10, "italic"), text_color='#B0B0B0',
            expand_x=True)],
        [sp.Text('Carpeta con modelo RNA exportado:', font=("Arial", 12))],
        [sp.Input(key='pso-RUTA_RNA-', size=(40, 1), font=("Arial", 12)),
         sp.FolderBrowse('Examinar', size=(10, 1))],
        [sp.Button('Cargar modelo RNA', key='pso-CARGAR_RNA-', size=(20, 1)),
         sp.Button('Quitar modelo',    key='pso-QUITAR_RNA-',  size=(15, 1))],
        [sp.Column(
            [[sp.Button('Editar config PSO del modelo',
                        key='pso-EDITAR_CONFIG-', size=(28, 1))]],
            key='pso-PIN_EDITAR-',
            visible=mostrar_editar_config,
            pad=(0, 0),
        )],
        [sp.Multiline(
            size=(60, 3), key='pso-INFO_RNA-', disabled=True,
            autoscroll=True, font=("Arial", 10),
            expand_x=True,
            # Mensaje inicial — se actualiza al cargar/quitar el modelo
            default_text=rna_info,
        )],
    ]
    frame_0 = sp.Frame(
        'Importación de RNA (opcional)', importacion,
        key='pso-FRAME-0-', visible=True,
        font=("Arial", 12, "bold"),
        expand_x=True,
    )

    # ------------------------------------------------------------------
    # Sección 1: Controles (siempre visible)
    # ------------------------------------------------------------------
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
        'Controles', controles,
        key='pso-FRAME-1-', visible=True,
        font=("Arial", 12, "bold"),
        expand_x=True,
    )

    # ------------------------------------------------------------------
    # Botones de acción
    # ------------------------------------------------------------------
    botones_accion = [
        sp.Button('Iniciar PSO',         size=(12, 1), key='pso-INI-'),
        sp.Button('Importar Datos',      size=(12, 1), key='pso-IMPORTAR-'),
        sp.Button('Controles Avanzados', size=(15, 1), key='pso-CONTROLES-'),
        sp.Button('Limpiar Datos',       size=(12, 1), key='pso-LIMPIAR-'),
    ]

    # ------------------------------------------------------------------
    # Panel de progreso (NUEVO)
    # ------------------------------------------------------------------
    progreso_layout = [
        [sp.Text('Estado:', size=(9, 1), font=("Arial", 11, "bold")),
         sp.Text('En espera...', key='pso-ESTADO-',
                 font=("Arial", 11), expand_x=True)],
        [sp.ProgressBar(1, orientation='h', size=(40, 18),
                        key='pso-PROGRESO-', expand_x=True,
                        bar_color=('#3B82F6', '#1F2937')),
         sp.Text('0%', key='pso-PORCENTAJE-', size=(6, 1),
                 font=("Arial", 11), justification='right')],
    ]
    frame_prog = sp.Frame(
        'Progreso del PSO', progreso_layout,
        font=("Arial", 12, "bold"),
        expand_x=True,
    )

    # ------------------------------------------------------------------
    # Sección 2: Límites de variables (columna derecha)
    # ------------------------------------------------------------------
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
                       size=(400, 500), expand_x=True, expand_y=True)

    # ------------------------------------------------------------------
    # Composición
    # ------------------------------------------------------------------
    col_izq = sp.Column([
        [frame_0],
        [frame_1],
        [sp.Column([botones_accion], expand_x=True)],
        [frame_prog],
    ], vertical_alignment='top', expand_x=True)

    col_der = sp.Column([
        [frame_2],
    ], vertical_alignment='top', expand_x=True)

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