# Restricciones del proyecto PSO + RNA

> Documento que centraliza todas las **reglas explícitas** que el sistema
> respeta: validaciones de entrada, dominios matemáticos, formatos de
> archivos, invariantes internas, restricciones de entorno y de seguridad.
>
> No describe estructura estática (ver `ARCHITECTURE.md`) ni flujos
> operativos (ver `WORKFLOWS.md`).

---

## 1. Propósito y alcance

Este documento es la **referencia única** de todo lo que el sistema acepta,
rechaza o exige. Cada restricción aquí listada debería poder convertirse en
un test automático.

**Alcance**:

- Reglas numéricas y de tipos.
- Dominios de la función objetivo simbólica.
- Formatos de archivos leídos y escritos.
- Invariantes internas del código.
- Entorno de ejecución y empaquetado.
- Decisiones de diseño que condicionan futuras extensiones.
- Límites de seguridad del parser.

**Fuera de alcance**:

- Estructura de módulos (→ `ARCHITECTURE.md`).
- Secuencias de uso (→ `WORKFLOWS.md`).
- Riesgos y mitigaciones (→ `RISKS.md`).

---

## 2. Restricciones numéricas y de tipos

Toda entrada numérica se valida antes de iniciar el cómputo. Un valor fuera
de rango produce un `popup_error` y detiene el flujo.

### 2.1 Optimizador PSO

| Regla | Se valida en | Mensaje |
|---|---|---|
| `NP ≥ 1` (entero) | `pso_runner._ejecutar_pso` | Error de conversión → popup |
| `NI ≥ 1` (entero) | `pso_runner._ejecutar_pso` | Error de conversión → popup |
| `NV ≥ 1` (entero) | `pso_runner._ejecutar_pso` | Error de conversión → popup |
| `len(lim_inf) == len(lim_sup) == NV` | `pso_runner._ejecutar_pso` | Error de longitud → popup |
| `lim_inf[i] < lim_sup[i]` para todo `i` | `pso_runner._ejecutar_pso` | `"Límite inf de x{i+1} >= sup."` |
| `RONDAS ≥ 1` (entero) | `pso_runner._ejecutar_pso` | `"Las rondas para parada temprana deben ser mayores que cero."` |
| `C1 ≥ 0`, `C2 ≥ 0` | `pso_runner._ejecutar_pso` | `"Los coeficientes c1 y c2 no pueden ser negativos."` |
| `TOL > 0` | `pso_runner._ejecutar_pso` | `"La tolerancia debe ser mayor que cero."` |
| `OPT ∈ {'Minimización', 'Maximización'}` | `Enjambre_M.evaluar_enjambre` | Excepción → popup |

### 2.2 Constructor RNA

| Regla | Se valida en | Mensaje |
|---|---|---|
| `NV ≥ 1` (entero) | `rna_runner._generar_rna` | Popup |
| `len(lim_inf) == len(lim_sup) == NV` | `rna_runner._generar_rna` | `"El número de variables debe coincidir con la cantidad de límites."` |
| `lim_inf[i] < lim_sup[i]` para todo `i` | `rna_runner._generar_rna` | `"Cada límite inferior debe ser menor que su límite superior."` |
| `capas ≥ 1` (entero) | `rna_runner._generar_rna` | Popup |
| `neuronas[i] ≥ 1` para todo `i` | `rna_runner._generar_rna` | `"Las capas y las neuronas deben ser mayores que cero."` |
| `len(neuronas) == capas` | `rna_runner._generar_rna` | `"El numero de neuronas debe coincidir con el numero de capas."` |
| `epocas ≥ 1` (entero) | `rna_runner._generar_rna` | `"Las épocas y el tamaño del batch deben ser mayores que cero."` |
| `batch ≥ 1` (entero) | `rna_runner._generar_rna` | Idem |
| `muestras ≥ 1` (entero) | `rna_runner._generar_rna` | `"El numero de muestras debe ser mayor que cero."` |

### 2.3 Predicción RNA

| Regla | Se valida en | Mensaje |
|---|---|---|
| Nº de valores introducidos == `estado.rna_nv` | `rna_runner._predecir` | `"Ingrese exactamente {nv} valores."` |
| Todos los valores son parseables a `float` | `rna_runner._predecir` | Error de conversión → popup |

### 2.4 Restricciones detectadas empíricamente

A diferencia de las reglas anteriores, estas **no se validan en el código**
pero conviene conocerlas porque producen degradación de la calidad del
resultado. Se dejan anotadas aquí como candidatas a formalizarse más
adelante; su tratamiento completo corresponde a `RISKS.md`.

- **`NV` alto (> 20)**: el PSO converge notablemente más lento y necesita
  `NP` proporcionalmente mayor. No hay validación, pero conviene advertir
  al usuario.
- **`NP` muy bajo (< 5)**: el enjambre pierde diversidad y puede quedar
  atrapado en mínimos locales. El usuario debe escoger `NP` en función de
  `NV` y del presupuesto computacional.
- **`NI` muy alto sin parada temprana**: el PSO sigue iterando aunque el
  mejor valor no mejore durante cientos de iteraciones.
- **RNA con `muestras < 100`**: el modelo generaliza mal; la pérdida de
  validación puede divergir respecto a la de entrenamiento.
- **RNA con `epocas < 10`**: el modelo no alcanza a ajustar ni siquiera
  funciones simples.
- **Modelo RNA extrapolando**: si el PSO explora fuera del rango
  `[lim_inf, lim_sup]` con el que se entrenó la RNA, las predicciones
  pueden ser arbitrarias (el escalador no cubre esos valores). El usuario
  debe ser consciente de que los límites del PSO deben coincidir con los
  del entrenamiento.

### 2.5 Rango recomendado de los límites

Los límites `lim_inf[i]` y `lim_sup[i]` no tienen un máximo impuesto por
el código. Sin embargo, se recomienda mantenerse en los siguientes rangos
para evitar confusión a usuarios sin conocimientos de optimización:

| Rango | Recomendación |
|---|---|
| `|lim| ≤ 1e3` | Rango por defecto. Es el que el sistema usa cuando no se especifica. |
| `1e3 < |lim| ≤ 1e4` | Aceptable, pero requiere ajustar `NP` y `NI` al alza. |
| `1e4 < |lim| ≤ 1e6` | Puede producir problemas numéricos en el cálculo de la inercia y en la escala de las partículas. |
| `|lim| > 1e6` | No recomendado. El enjambre pierde precisión y la función objetivo puede devolver `inf`. |

Los límites del PSO deben coincidir con el dominio con el que se entrenó el
modelo RNA, si se usa uno.

---

## 3. Dominios de la función objetivo

El parser vive en `PSO_MV/funcion_objetivo.py` y usa el módulo `ast` de la
biblioteca estándar. Su objetivo es doble: **compilar** expresiones
matemáticas simples y **rechazar** cualquier construcción que pudiera
ejecutar código arbitrario.

### 3.1 Nodos AST permitidos

Lista blanca cerrada. Cualquier nodo fuera de esta lista produce
`ValueError: 'La expresión contiene una operación no permitida.'`.

- `ast.Expression`
- `ast.BinOp`
- `ast.UnaryOp`
- `ast.Add`
- `ast.Sub`
- `ast.Mult`
- `ast.Div`
- `ast.Pow`
- `ast.Mod`
- `ast.USub`
- `ast.UAdd`
- `ast.Constant`
- `ast.Name`
- `ast.Call`

### 3.2 Variables y funciones

- **Variables**: `x1, x2, ..., xn` donde `n = nv`. Cualquier otro nombre
  produce `ValueError`.
- **Funciones**: `abs`, `cos`, `exp`, `log`, `sin`, `sqrt`, `tan`. Cualquier
  otra produce `ValueError`.
- Cada función debe recibir **un único argumento**. Las llamadas con más
  argumentos o con `keywords` producen `ValueError`.

### 3.3 Dominios matemáticos

Dos funciones tienen dominio restringido y se verifican antes de evaluar:

| Función | Condición | Mensaje |
|---|---|---|
| `log(arg)` | `arg > 0` | `"El argumento de log debe ser mayor que cero."` |
| `sqrt(arg)` | `arg ≥ 0` | `"El argumento de sqrt debe ser mayor o igual que cero."` |

Si un punto de prueba o una partícula del enjambre cae fuera del dominio,
la evaluación lanza `ValueError` que `pso_runner` captura y muestra como
`"Una partícula salió del dominio permitido de la función objetivo."`.

### 3.4 Prohibiciones

Explícitamente no permitidas:

- Acceso a atributos (`obj.attr`).
- Subíndices (`arr[0]`).
- Lambdas.
- Comprensiones de listas, diccionarios o generadores.
- Bloques `if`, `for`, `while`.
- Asignaciones.
- Llamadas a métodos encadenados.
- Cualquier referencia a `__builtins__` o nombres dunder.

### 3.5 Resultado esperado

La función objetivo compilada:

- Recibe un `np.ndarray` con `nv` componentes.
- Devuelve un único valor `float`.
- Ese valor debe ser finito (`np.isfinite`); en caso contrario se lanza
  `ValueError: 'La evaluación de la función no produjo un valor finito.'`.

### 3.6 Extensibilidad futura

La lista de funciones permitidas y la lista de nodos AST son **cerradas**
en la versión actual. Ampliarlas (por ejemplo, añadir `arcsin`, `arctan`,
`sinh`, `cosh`, `tanh`, o constantes como `pi`, `e`) requiere:

1. Añadir la función a `_FUNCIONES_PERMITIDAS`.
2. Si tiene dominio restringido, añadir su condición a
   `_CONDICIONES_DOMINIO`.
3. Actualizar este documento y la tabla de la sección 3.2.

No se permite inyectar funciones en tiempo de ejecución ni cargar expresiones
desde archivos externos.

---

## 4. Formatos de archivo

### 4.1 `config.json` (modelo RNA exportado)

Estructura obligatoria:

```json
{
  "tipo": "RNA",
  "version": 1,
  "nv": 3,
  "lim_inf": [-5, -5, -5],
  "lim_sup": [ 5,  5,  5],
  "columnas_x": ["x1", "x2", "x3"],
  "pso": {
    "NP": 30, "NI": 50, "OPT": "Minimización",
    "W_I": 0.9, "W_F": 0.4, "C1": 1.5, "C2": 1.5,
    "RONDAS": 10, "TOL": 1e-6, "RED_W": true, "P_T": false
  }
}
```

| Campo | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `tipo` | string | Sí | Debe ser `"RNA"`. |
| `version` | int | Sí | Debe ser `1`. |
| `nv` | int | Sí | `≥ 1`. |
| `lim_inf`, `lim_sup` | list[float] | Sí | `len == nv`; `lim_inf[i] < lim_sup[i]`. |
| `columnas_x` | list[string] | Sí | `len == nv`. Ver 4.4. |
| `pso` | dict | Opcional | Bloque de parámetros sugeridos. |

Si `tipo` no es `"RNA"`, `Hibrido.cargar_funcion_prediccion` lanza
`ValueError` y la carga falla.

Si falta `modelo.keras`, `scaler_x.save` o `scaler_y.save`, la carga
falla con `FileNotFoundError`.

### 4.2 CSV de parámetros del PSO

Dos columnas obligatorias:

| Columna | Contenido |
|---|---|
| `parametro` | Nombre del parámetro (sin el prefijo `pso-`) |
| `valor` | Valor en representación textual |

Parámetros reconocidos: `NP`, `NI`, `NV`, `FUNCION`, `OPT`, `D_W`, `P_T`,
`HIST`, `MIN_0..MIN_{NV-1}`, `MAX_0..MAX_{NV-1}`.

Los booleanos (`D_W`, `P_T`, `HIST`) deben ser `True` o `False`
(mayúscula o minúscula, indistinto).

### 4.3 CSV de datos para RNA

- Al menos **una columna de entrada** y **una columna objetivo**.
- Todas las columnas de entrada y la objetivo deben ser **numéricas**.
- **Sin valores faltantes** (`NaN`).
- La columna objetivo se selecciona en el combo `rna-COL_Y-`; si no hay
  selección, se usa la **última columna**.

### 4.4 Sobre las columnas de entrada

`config.json` acepta **nombres arbitrarios** en `columnas_x`, porque un
usuario puede entrenar una RNA con un CSV cuyas columnas se llamen
`temperatura`, `presion`, `caudal`, etc.

Sin embargo, el modelo entrenado **no conserva la semántica** de esos
nombres. Al usarse como función objetivo del PSO, las variables internas
del enjambre siguen llamándose `x1, x2, ..., xn`; el orden posicional de
`columnas_x` es lo único que preserva la correspondencia.

**Consecuencias prácticas**:

- El usuario debe recordar qué columna correspondía a cada `xi` si quiere
  interpretar los resultados del PSO en términos del dominio original.
- En el modo sintético del tab RNA, `columnas_x` se rellena
  automáticamente con `x1, x2, ..., xn`.
- En el modo importado, se rellena con los nombres reales del CSV, en el
  mismo orden en que aparecen las columnas de entrada.

### 4.5 Nota sobre versionado

El campo `version` existe para permitir evoluciones futuras del formato.
La versión actual es `1`. Cualquier cambio incompatible (renombrar campos,
cambiar tipos, eliminar campos) obliga a incrementar `version` y a
implementar una migración en `Hibrido.cargar_funcion_prediccion`.

---

## 5. Invariantes del sistema

Reglas que deben cumplirse en todo momento. Su violación es señal de bug.

### 5.1 Sobre la UI

- El canvas `res-CANVAS-` y el multiline `res-OUTPUT-` existen **solo** en
  el tab Resultados.
- Las claves de widgets llevan siempre prefijo (`pso-`, `rna-`, `res-`).
  Nunca hay claves sin prefijo.
- Los layouts en `ui/` son puramente declarativos: no contienen lógica
  condicional, bucles de negocio, ni acceso a `estado`.

### 5.2 Sobre el estado

- `estado.funcion_objetivo_rna` es `None` o un `Callable` que recibe un
  `np.ndarray` y devuelve un `float` finito.
- `estado.defaults` contiene siempre las claves base:
  `pso-MODO_BASICO-`, `pso-MODO_IMPORTADO-`, `pso-OPT-`, `pso-NP-`,
  `pso-NI-`, `pso-FUNCION-`, `pso-D_W-`, `pso-HIST-`, `pso-P_T-`,
  `pso-W_I-`, `pso-W_F-`, `pso-C1-`, `pso-C2-`, `pso-RED_W-`,
  `pso-RONDAS-`, `pso-TOL-`.
- `estado.nv == 0` implica que no existen inputs `pso-MIN-i-` ni
  `pso-MAX-i-` en la UI.
- `estado.ultima_figura` solo se actualiza dentro de
  `pso_runner.actualizar_grafica`.
- El CSV `Historial_Enjambre.csv` se escribe siempre en
  `resultados_pso/`, nunca en el directorio de trabajo.

### 5.3 Sobre los handlers

- Los handlers de `pso_runner` y `rna_runner` **nunca crean ventanas**.
  Solo manipulan la ventana recibida como parámetro.
- Los handlers **nunca cierran la ventana principal**. Si un flujo requiere
  reconstrucción, devuelven `'REBUILD'` y es `app.py` quien la ejecuta.
- Las validaciones numéricas se hacen **antes** de instanciar el enjambre
  o el modelo de Keras. Un error de validación no debe dejar recursos a
  medio construir.

### 5.4 Retornos de handlers

Los handlers `pso_runner.handle()` y `rna_runner.handle()` devuelven
únicamente uno de estos valores:

| Retorno | Significado |
|---|---|
| `None` | Sin acción adicional; el bucle continúa. |
| `'REBUILD'` | Reconstruir la ventana conservando `estado`. |
| `'IR_A_RNA'` | Cambiar programáticamente al tab Constructor RNA. |

Cualquier otro valor se considera bug.

---

## 6. Restricciones de entorno

### 6.1 Versiones de dependencias

| Dependencia | Versión mínima | Comentario |
|---|---|---|
| Python | 3.10 | Uso de `match/case` en algunos módulos. |
| PySimpleGUI | 4.60 | `sg.pin` con `key` no está en versiones antiguas; se usa `sg.Column` como alternativa. |
| TensorFlow | 2.13 | Formato `.keras` como formato de guardado. |
| scikit-learn | 1.3 | `StandardScaler` serializado con joblib. |
| joblib | 1.3 | Formato `.save`. |
| matplotlib | 3.7 | Backend Tk para incrustar en PySimpleGUI. |
| pandas | 2.0 | Uso de `to_numpy(dtype=...)`. |
| numpy | 1.24 | `np.isfinite`, `np.asarray`. |

Los `StandardScaler` serializados con joblib pueden dejar de cargarse si
se cambia de versión mayor de scikit-learn. Si eso ocurre, el modelo debe
reentrenarse y reexportarse.

### 6.2 Plataforma

- Windows / Linux / macOS con backend Tk instalado.
- Codificación UTF-8 en todos los archivos `.py` y `.json`.
- Terminal con soporte de colores ANSI (opcional; la GUI no los usa).

### 6.3 Empaquetado `.exe`

El proyecto se concibe para ser empaquetable como ejecutable único. Reglas
derivadas:

- Todas las rutas deben ser **relativas al directorio de trabajo del
  usuario**, no al directorio del bundle.
- `resultados_pso/` y `exportaciones/` se crean en el cwd, no dentro del
  ejecutable.
- El backend Tk, las fuentes de matplotlib y los recursos de TensorFlow
  deben incluirse en el bundle.
- TensorFlow añade en torno a 500 MB al tamaño final. Puede ser necesario
  dividir la aplicación en dos ejecutables (PSO y RNA) si el tamaño es
  prohibitivo.

---

## 7. Anexo: decisiones de diseño

Registro breve de las decisiones que condicionan el diseño actual. Cada
una sigue el formato *Architecture Decision Record* (ADR) simplificado:
contexto, decisión y consecuencias.

### D-001 — Una sola ventana con `TabGroup`

**Contexto**: el proyecto nació como dos GUIs independientes
(`mainGUI.py` y `RNAGUI.py`) con estado global duplicado.

**Decisión**: unificar en `app.py` con un único `sg.TabGroup` y tres
pestañas.

**Consecuencias**:

- (+) Estado en memoria compartido entre tabs.
- (+) Un solo bucle de eventos y una sola política de cierre.
- (−) Obligación de prefijar claves para enrutar eventos.

### D-002 — Prefijos de claves como mecanismo de enrutamiento

**Contexto**: con una sola ventana, las claves de widgets de distintos tabs
pueden colisionar (ambos tabs tenían `-FUNCION-`, `-NV-`, `-CANVAS-`, etc.).

**Decisión**: prefijar todas las claves con `pso-`, `rna-` o `res-` y
enrutar en `app.py` según el prefijo.

**Consecuencias**:

- (+) Enrutamiento trivial sin tabla de mapeo.
- (+) Añadir un tab nuevo es mecánico: nuevo prefijo, nuevo runner.
- (−) Las claves son más largas y verbosas.

### D-003 — Estado compartido como singleton

**Contexto**: se necesitaba comunicar información entre tabs (por ejemplo,
el modelo RNA entrenado en el tab RNA debe ser visible desde el tab PSO)
sin acoplar los módulos.

**Decisión**: un único objeto `estado` en `estado.py`, importado por los
runners. Se modifica in situ; no hay inyección de dependencias.

**Consecuencias**:

- (+) Simplicidad para un proyecto de una sola persona.
- (+) Los `REBUILD` de ventana no pierden información.
- (−) Difícil de testear en aislamiento.
- (−) Los campos deben documentarse y resetearse explícitamente.

### D-004 — `config.json` como contrato RNA → PSO

**Contexto**: el modelo RNA entrenado debe poder usarse como función
objetivo del PSO en sesiones distintas, incluso reiniciando la aplicación.

**Decisión**: al exportar el modelo, escribir un `config.json` que
describe `nv`, límites, columnas y parámetros PSO sugeridos. `Hibrido`
lo lee al cargar y reconstruye la función objetivo.

**Consecuencias**:

- (+) Independencia entre sesiones: no hace falta mantener viva la RNA
  entrenada.
- (+) El `config.json` es inspeccionable y editable a mano.
- (−) Obliga a mantener un formato estable con campo `version`.
- (−) Los modelos exportados con versiones antiguas pueden requerir
  migración.

### D-005 — `REBUILD` como mecanismo de cambio estructural

**Contexto**: cambiar `NV` requiere regenerar los widgets de límites
(`pso-MIN-i-`, `pso-MAX-i-`). PySimpleGUI no permite añadir widgets a un
layout ya construido.

**Decisión**: los handlers devuelven `'REBUILD'` y `app.py` cierra la
ventana, la reconstruye con el layout actualizado y restaura el estado
persistente (figura del tab Resultados).

**Consecuencias**:

- (+) La UI siempre refleja el estado actual.
- (+) El código de los handlers permanece lineal: valida, muta estado,
  devuelve `'REBUILD'`.
- (−) El multiline de salida se vacía con cada `REBUILD`.
- (−) El coste de reconstruir la ventana es perceptible (~200 ms).

### D-006 — Rutas relativas al cwd para portabilidad

**Contexto**: el objetivo final es distribuir la suite como ejecutable
portátil. El ejecutable puede estar en una ruta sin permisos de escritura
(por ejemplo, `Program Files`).

**Decisión**: todas las escrituras (`resultados_pso/`, `exportaciones/`)
se hacen relativas al **directorio de trabajo del usuario**, no a la
ruta del ejecutable.

**Consecuencias**:

- (+) Funciona desde cualquier ubicación del ejecutable.
- (+) Los archivos generados son fáciles de localizar.
- (−) Los artefactos generados no acompañan al ejecutable si este se mueve.

---

## 8. Restricciones de seguridad

El sistema asume un **usuario de confianza en una máquina local**. No hay
autenticación, cifrado ni aislamiento entre procesos. Aun así, se aplican
las siguientes reglas para minimizar superficie de ataque.

### 8.1 Parser de función objetivo

El parser AST evita la ejecución de código arbitrario mediante una lista
blanca de nodos y nombres. **No es un sandbox perfecto**: la evaluación se
hace con `eval` sobre un entorno controlado, pero confía en que
`numpy` y sus operaciones son seguras.

Restricciones adicionales:

- El diccionario de evaluación usa `{'__builtins__': {}}` para bloquear
  funciones integradas de Python.
- Los nombres permitidos son únicamente las variables `x1..xn` y las
  funciones matemáticas listadas en la sección 3.2.
- No se permite importar módulos ni acceder a atributos.

### 8.2 Modelos de RNA cargados

`Hibrido.cargar_funcion_prediccion` carga un modelo Keras y dos
`StandardScaler` desde disco. **No hay verificación de integridad**: si un
atacante reemplaza `modelo.keras` por otro archivo, el sistema lo cargará
sin sospechar. Este riesgo se acepta porque el modelo se produce en la
misma máquina que lo consume.

### 8.3 Archivos leídos

Todos los archivos (`config.json`, CSVs, modelos) se leen con los permisos
del usuario actual del sistema operativo. No hay elevación de privilegios.

### 8.4 Salidas escritas

- `resultados_pso/` y `exportaciones/` se crean con permisos por defecto
  del sistema operativo.
- Los CSV se escriben en UTF-8 sin BOM.
- Los JSON se escriben con `ensure_ascii=False` para preservar tildes.

### 8.5 Alcance fuera de cobertura

Las siguientes áreas **no** están protegidas:

- Ataques de canal lateral (tiempos de ejecución).
- Manipulación de los archivos generados entre sesiones.
- Ataques sobre el entorno de Python (por ejemplo, inyección de módulos
  en `sys.path`).
- Red: la aplicación no abre puertos ni conexiones salientes.

Si en el futuro la suite se distribuye a terceros, esta sección debe
revisarse antes de cualquier release pública.