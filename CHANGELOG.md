# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [Unreleased]

### Added
- (aquí irán los cambios de la próxima versión)

### Changed
- (aquí van los cambios de comportamiento)

### Fixed
- (aquí van los arreglos de bugs)

---

## [v0.1.0] - 2026-09-28

Primera versión funcional de la suite **PSO + RNA**.

### Added

#### Interfaz general
- Ventana única con `TabGroup` y tres pestañas intercambiables:
  - **Optimizador PSO**
  - **Constructor RNA**
  - **Resultados**
- Enrutamiento de eventos por prefijo (`pso-`, `rna-`, `res-`) desde `app.py`.
- Estado compartido entre pestañas (`estado.py`).

#### Optimizador PSO
- Función objetivo simbólica con parser seguro (`ast`).
- Función objetivo basada en modelo de red neuronal exportado.
- Panel de **progreso en vivo**: barra + porcentaje + mejor valor por iteración.
- Controles avanzados (inercia, coeficientes cognitivo/social, parada temprana).
- Límites por variable con scroll vertical.
- Importación/exportación de parámetros en CSV.
- Edición del bloque `pso` del `config.json` del modelo RNA cargado.
- Guardado automático del historial en `resultados_pso/Historial_Enjambre.csv`.
- Callback `iteracion_callback` en `Enjambre_M.optimizar()` para retroalimentación.

#### Constructor RNA
- Dataset sintético a partir de una función matemática y límites.
- Dataset importado desde CSV.
- Entrenamiento con Keras/TensorFlow (capas, neuronas, activación configurables).
- Gráfica de pérdida (entrenamiento vs validación) en vivo.
- Validación por predicción manual.
- Exportación del modelo en 4 archivos:
  - `modelo.keras`
  - `scaler_x.save`
  - `scaler_y.save`
  - `config.json` (con límites, columnas y parámetros PSO sugeridos)

#### Resultados
- Multiline de salida y canvas de gráfica en dos columnas.
- Botón **Guardar gráfica (PNG)** → `resultados_pso/grafica_enjambre.png` a 150 dpi.
- Botón **Limpiar salida** para vaciar el multiline.
- Persistencia de la figura entre reconstrucciones de ventana.

#### Integración RNA ↔ PSO
- El tab PSO detecta y carga un modelo exportado desde el tab RNA.
- Autorelleno de `NP`, `NI`, `OPT`, `NV`, límites y controles avanzados
  a partir del bloque `pso` del `config.json`.
- Botón **Quitar modelo** para volver a la función simbólica.

### Changed
- `PSO_MV/Enjambre_M.py` acepta el parámetro `carpeta_salida` y guarda el CSV
  de historial en `resultados_pso/` (antes: directorio de trabajo).
- `PSO_MV/Enjambre_M.py` acepta `iteracion_callback` para notificar progreso.

### Fixed
- Eliminada la colisión de claves entre los layouts de PSO y RNA mediante prefijos.
- Corregido el uso de `sp.pin` (reemplazado por `sp.Column` con `key` para
  compatibilidad con versiones antiguas de PySimpleGUI).

---

[v0.1.0]: https://github.com/teniapc07-debug/pso-rna-suite.git/releases/tag/v0.1.0