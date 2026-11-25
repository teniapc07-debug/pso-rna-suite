import FreeSimpleGUI as sg

def crear_layout_masa():
    """
    Crea el layout para la pestaña del Módulo Auxiliar de Aumento (MASA).
    """
    header_font = ("Helvetica", 12, "bold")
    
    # --- Sección de Carga de Archivo ---
    frame_carga = [
        [sg.Text("Paso 1: Cargar Dataset (CSV o Excel)", font=header_font)],
        [
            sg.Input(key="-MASA_FILE_PATH-", enable_events=True, visible=False),
            sg.FileBrowse(
                "Buscar Archivo", 
                file_types=(("Archivos de Datos", "*.csv *.xlsx *.xls"), ("Todos", "*.*")),
                key="-MASA_BROWSE-",
                target="-MASA_FILE_PATH-"
            ),
            sg.Text("Ningún archivo seleccionado", key="-MASA_FILE_NAME-", size=(40, 1), text_color="gray")
        ]
    ]

    # --- Sección de Vista Previa ---
    frame_preview = [
        [sg.Text("Vista Previa de los Datos (primeras 5 filas):", font=header_font)],
        [sg.Multiline(size=(70, 6), key="-MASA_PREVIEW-", disabled=True, font=("Courier", 10))]
    ]

    # --- Sección de Configuración de Columnas y Parámetros ---
    frame_config = [
        [sg.Text("Paso 2: Configurar Columnas y Parámetros", font=header_font)],
        [
            sg.Column([
                [sg.Text("Variable Objetivo (Y):")],
                [sg.Combo([], key="-MASA_TARGET_COL-", size=(25, 1), readonly=True)]
            ], pad=(0, 10)),
            
            sg.Column([
                [sg.Text("Variables de Entrada (X): (Ctrl+Clic para varias)")],
                [sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-MASA_FEATURE_COLS-", size=(30, 4))]
            ], pad=(0, 10))
        ],
        [sg.HorizontalSeparator(pad=(0, 10))],
        [
            sg.Text("Cantidad de datos sintéticos a generar:"),
            sg.InputText(default_text="50000", key="-MASA_N_SAMPLES-", size=(10, 1)),
        ]
    ]

    # --- Sección de Ejecución y Estado ---
    frame_ejecucion = [
        [
            sg.Button("Ejecutar MASA y Generar Dataset", key="-MASA_RUN-", button_color=("white", "#2E8B57"), size=(30, 1)),
            sg.Button("Limpiar", key="-MASA_CLEAR-")
        ],
        [sg.Text("Estado: Esperando acción...", key="-MASA_STATUS-", text_color="blue", size=(60, 2))]
    ]

    # --- Layout Principal (CORREGIDO AQUÍ) ---
    # Nota que ahora pasamos 'frame_carga' directamente, sin los corchetes []
    layout = [
        [sg.Frame("", frame_carga, expand_x=True, relief=sg.RELIEF_SUNKEN)],
        [sg.Frame("", frame_preview, expand_x=True, relief=sg.RELIEF_SUNKEN)],
        [sg.Frame("", frame_config, expand_x=True, relief=sg.RELIEF_SUNKEN)],
        [sg.Frame("", frame_ejecucion, expand_x=True, relief=sg.RELIEF_SUNKEN)]
    ]
    
    return layout