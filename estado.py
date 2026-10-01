# estado.py
import PySimpleGUI as sg


class OutputGUI:
    """Redirige stdout/stderr a un Multiline de PySimpleGUI."""
    def __init__(self, window, key, stream=None):
        self.window = window
        self.key = key
        self.stream = stream
        self.buffer = ''

    def write(self, message):
        if not message:
            return
        if self.stream is not None:
            self.stream.write(message)
        try:
            self.buffer += message.replace('\r\n', '\n')
            self.window[self.key].update(self.buffer)
        except Exception:
            if self.stream is not None:
                self.stream.write(f"[ERROR_OUTPUT_GUI] {message}")

    def flush(self):
        if self.stream is not None:
            self.stream.flush()


class Estado:
    def __init__(self):
        # --- PSO ---
        self.nv = 0
        self.tab_actual = 'pso-TAB-'
        self.defaults = {
            'pso-MODO_BASICO-':    True,
            'pso-MODO_IMPORTADO-': False,
            'pso-OPT-':            'Minimización',
            'pso-NP-':             '',
            'pso-NI-':             '',
            'pso-FUNCION-':        '',
            'pso-D_W-':            False,
            'pso-HIST-':           False,
            'pso-P_T-':            False,
            'pso-W_I-':            '0.9',
            'pso-W_F-':            '0.4',
            'pso-C1-':             '1.5',
            'pso-C2-':             '1.5',
            'pso-RED_W-':          True,
            'pso-RONDAS-':         '10',
            'pso-TOL-':            '1e-6',
        }

        # --- Función objetivo activa (simbólica o RNA) ---
        self.funcion_objetivo_rna = None
        self.ruta_rna = None
        self.rna_info_texto = 'No hay modelo RNA cargado. Se usará la función simbólica.'

        # --- RNA ---
        self.rna_datos_importados = None
        self.rna_modelo = None
        self.rna_escalador_x = None
        self.rna_escalador_y = None
        self.rna_X_validacion = None
        self.rna_y_validacion = None
        self.rna_nv = None
        self.rna_lim_inf_global = None
        self.rna_lim_sup_global = None
        self.rna_columnas_x_global = None

        # --- Resultados (figura persistente) ---
        self.ultima_figura = None
        self.ultimo_dtframe = None

estado = Estado()