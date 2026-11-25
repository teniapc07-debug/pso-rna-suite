import pandas as pd
import os
import FreeSimpleGUI as sg
from MASA.masa_manager import MASAManager
from MASA.gpr_surrogate import GPRSurrogate
from estado import estado # <--- IMPORTACIÓN FALTANTE
from logica import rutas # <--- IMPORTAMOS RUTAS PARA USAR TU SISTEMA DE CARPETAS

def manejar_eventos_masa(event, values, window):
    """
    Maneja los eventos específicos de la pestaña MASA.
    """
    
    # 1. EVENTO: Cargar archivo
    if event == "-MASA_FILE_PATH-":
        filepath = values["-MASA_FILE_PATH-"]
        if not filepath:
            return True
            
        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(filepath)
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(filepath)
            else:
                raise ValueError("Formato no soportado.")

            window["-MASA_FILE_NAME-"].update(os.path.basename(filepath))
            preview_text = df.head(5).to_string()
            window["-MASA_PREVIEW-"].update(preview_text)
            
            columnas = list(df.columns)
            window["-MASA_TARGET_COL-"].update(values=columnas)
            window["-MASA_FEATURE_COLS-"].update(values=columnas)
            
            window["-MASA_STATUS-"].update("Archivo cargado correctamente. Configure las columnas.", text_color="green")

        except Exception as e:
            window["-MASA_STATUS-"].update(f"Error al cargar: {str(e)}", text_color="red")
            sg.popup_error(f"No se pudo leer el archivo:\n{str(e)}")
        
        return True

    # 2. EVENTO: Ejecutar MASA
    elif event == "-MASA_RUN-":
        filepath = values["-MASA_FILE_PATH-"]
        target_col = values["-MASA_TARGET_COL-"]
        feature_cols = values["-MASA_FEATURE_COLS-"]
        n_samples_str = values["-MASA_N_SAMPLES-"]

        # --- Validaciones Previas ---
        if not filepath:
            sg.popup_error("Por favor, carga un archivo primero.")
            return True
        
        if not target_col:
            sg.popup_error("Debes seleccionar una Variable Objetivo (Y).")
            return True
            
        if not feature_cols:
            sg.popup_error("Debes seleccionar al menos una Variable de Entrada (X).")
            return True

        if target_col in feature_cols:
            sg.popup_error("La Variable Objetivo no puede estar también en las Variables de Entrada.")
            return True

        try:
            n_samples = int(n_samples_str)
            if n_samples <= 0:
                raise ValueError()
        except ValueError:
            sg.popup_error("La cantidad de datos sintéticos debe ser un número entero positivo.")
            return True

        # --- Ejecución ---
        window["-MASA_STATUS-"].update("⏳ Ejecutando MASA... Esto puede tardar unos segundos.", text_color="orange")
        window.refresh()

        try:
            modelo_auxiliar = GPRSurrogate()
            manager = MASAManager(surrogate_model=modelo_auxiliar)
            
            # Usamos tu módulo de rutas
            try:
                carpeta_export = rutas.carpeta_datos()
            except AttributeError:
                # Fallback por si la función se llama distinto en tu rutas.py
                carpeta_export = "Output" 
                
            if not os.path.exists(carpeta_export):
                os.makedirs(carpeta_export)
                
            nombre_salida = f"Dataset_Aumentado_{os.path.splitext(os.path.basename(filepath))[0]}.csv"
            output_path = os.path.join(carpeta_export, nombre_salida)

            resultado = manager.run_augmentation_pipeline(
                filepath=filepath,
                feature_cols=feature_cols,
                target_col=target_col,
                n_samples=n_samples,
                output_path=output_path
            )

            msj = (f"✅ ¡Éxito! Se generaron {resultado['n_synthetic_samples']} datos.\n"
                   f"Guardado en: {resultado['output_path']}\n")
            
            window["-MASA_STATUS-"].update(msj, text_color="green")
            
            # --- AQUÍ ESTABA EL ERROR ---
            # Ahora guardamos en el estado global usando notación de punto
            estado.ruta_dataset_sintetico = output_path
            estado.hay_dataset_nuevo = True
            
            sg.popup("MASA finalizado con éxito", "El dataset sintético está listo para ser usado por la RNA.", title="Proceso Completado")

        except Exception as e:
            window["-MASA_STATUS-"].update(f"❌ Error en MASA: {str(e)}", text_color="red")
            sg.popup_error(f"Ocurrió un error durante la generación:\n{str(e)}")

        return True

    # 3. EVENTO: Limpiar Formulario
    elif event == "-MASA_CLEAR-":
        window["-MASA_FILE_PATH-"].update("")
        window["-MASA_FILE_NAME-"].update("Ningún archivo seleccionado")
        window["-MASA_PREVIEW-"].update("")
        window["-MASA_TARGET_COL-"].update(values=[], value="")
        window["-MASA_FEATURE_COLS-"].update(values=[], set_to_index=[])
        window["-MASA_N_SAMPLES-"].update("50000")
        window["-MASA_STATUS-"].update("Estado: Esperando acción...", text_color="blue")
        return True

    return False