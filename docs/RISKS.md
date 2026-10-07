# Riesgos del proyecto PSO + RNA

> Documento que cataloga los riesgos conocidos — técnicos, de dependencias,
> de uso y de mantenimiento — junto con su probabilidad, impacto y
> mitigación actual o prevista.
>
> No describe estructura estática (ver `ARCHITECTURE.md`), flujos
> operativos (ver `WORKFLOWS.md`) ni reglas internas (ver `CONSTRAINTS.md`).

---

## 1. Propósito y alcance

Este documento responde a una única pregunta: **¿qué puede salir mal y
qué estamos haciendo al respecto?**

**Alcance**:

- Riesgos de dependencias externas (bibliotecas, plataformas, licencias).
- Riesgos técnicos internos (diseño propio).
- Riesgos de uso (comportamiento del usuario final).
- Riesgos de mantenimiento (degradación con el tiempo).
- Matriz resumen y plan de mitigación priorizada.

**Fuera de alcance**:

- Riesgos de proyecto (plazos, alcance, entrega académica) — se tratarán
  por separado cuando se aborde la fase de tesis.
- Riesgos de seguridad ya cubiertos explícitamente en
  `CONSTRAINTS.md`, sección 8. Aquí solo se referencian.

**Contexto de uso**: la suite se distribuye para uso **local en una sola
máquina**, pero está previsto que la usen terceros (tribunal, compañeros,
usuarios sin perfil técnico). Esta condición eleva la probabilidad de
varios riesgos de entorno y licencia.

---

## 2. Clasificación de riesgos

Los riesgos se agrupan en cuatro categorías según su origen:

| Categoría | Origen | Ejemplo típico |
|---|---|---|
| **Dependencias externas** | Bibliotecas y plataformas de terceros | Cambio de API en TensorFlow |
| **Técnicos internos** | Decisiones de diseño propias | Estado global en `estado.py` |
| **De uso** | Acciones del usuario final | Límites incoherentes |
| **De mantenimiento** | Degradación del proyecto con el tiempo | Falta de tests |

### Escalas cualitativas

**Probabilidad**:

- **Baja**: poco probable que ocurra en un año de uso normal.
- **Media**: puede ocurrir en algún momento del ciclo de vida del proyecto.
- **Alta**: ocurrirá con seguridad si no se mitiga.

**Impacto**:

- **Bajo**: molesta al usuario, pero se puede seguir trabajando.
- **Medio**: interrumpe un flujo concreto; exige reinicio o reconfiguración.
- **Alto**: rompe la aplicación o produce resultados incorrectos.
- **Crítico**: pérdida de datos o imposibilidad de distribuir la suite.

---

## 3. Riesgos por categoría

Cada riesgo tiene un identificador `R-XX` para poder referenciarlo desde
otros documentos y desde los commits de mitigación.

### 3.1 Riesgos de dependencias externas

#### R-01 — Cambio de licencia de PySimpleGUI

**Descripción**: PySimpleGUI cambió a licencia propietaria a partir de la
versión 5.x (2024). Las versiones 4.x siguen bajo LGPL, pero ya no reciben
actualizaciones. Existe un fork MIT, **FreeSimpleGUI**, que mantiene la API
compatible.

**Probabilidad**: alta. El cambio ya ocurrió; el proyecto está en
PySimpleGUI 4.x por decisión, no por elección futura.

**Impacto**: crítico si se distribuye la suite pública o académicamente.

**Mitigación actual**: el proyecto usa FreeSimpleGUI, fork MIT del
PySimpleGUI 4.x original. Mantenimiento activo por la comunidad y
sin restricciones de licencia.

**Mitigación pendiente**:

- Evaluar la migración a `FreeSimpleGUI` si el desarrollo de PySimpleGUI
  se estanca o aparecen problemas de compatibilidad.
- Fijar la versión en `pyproject.toml` para evitar saltos no controlados.

#### R-02 — Cambios de API en TensorFlow

**Descripción**: TensorFlow 2.x ha evolucionado con cambios de firma en
`model.save`, carga de modelos y serialización. Un salto de versión mayor
(por ejemplo, 2.13 → 3.0) puede invalidar los `.keras` exportados.

**Probabilidad**: media.

**Impacto**: medio. Afecta al flujo RNA ↔ PSO: modelos viejos pueden no
cargar.

**Mitigación actual**: se fija `tensorflow ≥ 2.13` en `CONSTRAINTS.md`. El
formato `.keras` es el estándar actual.

**Mitigación pendiente**: cuando TensorFlow anuncie la versión 3.0,
reentrenar y reexportar los modelos antes de actualizar el `requirements`.
Documentar la versión exacta de TensorFlow en `config.json` (campo futuro
`tensorflow_version`).

#### R-03 — Incompatibilidad de `StandardScaler` serializado

**Descripción**: `joblib.dump` no garantiza compatibilidad de los objetos
`StandardScaler` entre versiones mayores de scikit-learn. Un modelo
exportado con sklearn 1.3 puede no cargar con sklearn 2.0.

**Probabilidad**: media. Ocurre cuando se actualiza la dependencia.

**Impacto**: alto. Rompe la carga de modelos exportados, obliga a
reentrenar.

**Mitigación actual**: se fija `scikit-learn ≥ 1.3` en `CONSTRAINTS.md`.

**Mitigación pendiente**: registrar la versión de scikit-learn en el
`config.json` al exportar. Al cargar, advertir si la versión del entorno
difiere.

#### R-04 — Backend Tk no disponible

**Descripción**: matplotlib necesita el backend Tk para incrustar figuras
en PySimpleGUI. En algunas distribuciones Linux mínimas o entornos
virtuales mal configurados, Tcl/Tk no está instalado.

**Probabilidad**: baja en Windows (incluye Tk por defecto). Alta si se
distribuye a entornos Linux sin escritorio.

**Impacto**: alto. La aplicación arranca pero falla al primer intento de
dibujar la gráfica.

**Mitigación actual**: PyInstaller empaqueta los binarios de Tcl/Tk en
el bundle. Verificado en carpeta limpia sin Python instalado.

**Mitigación pendiente**: ninguna. Riesgo controlado.


#### R-05 — Tamaño del ejecutable por TensorFlow

**Descripción**: TensorFlow añade ~500 MB al ejecutable final. Un `.exe`
de esa magnitud es incómodo de distribuir y lento de cargar en máquinas
modestas.

**Probabilidad**: alta si se empaqueta todo en un único ejecutable.

**Impacto**: medio. No impide el uso, pero complica la distribución.

**Mitigación actual**: se usa PyInstaller en modo `--onedir` con
`excludes` explícitos para backends de GUI no usados (PyQt, PySide,
Jupyter). El bundle final pesa ~1.3 GB.

**Mitigación pendiente**: si el tamaño resulta prohibitivo para
distribución, evaluar dividir la suite en dos ejecutables (uno ligero
con solo el PSO, otro con el motor RNA).

### 3.2 Riesgos técnicos internos

#### R-06 — Estado global no reseteado entre flujos

**Descripción**: `estado.py` mantiene información compartida entre tabs.
Si un flujo deja un campo a medias (por ejemplo, `rna_modelo` no se limpia
tras un error de entrenamiento), el siguiente flujo puede comportarse de
forma inesperada.

**Probabilidad**: media.

**Impacto**: medio. Bugs sutiles que solo se reproducen tras una secuencia
concreta.

**Mitigación actual**: los flujos documentados en `WORKFLOWS.md` limpian
explícitamente los campos relevantes al terminar o al fallar.

**Mitigación pendiente**: escribir tests que ejecuten secuencias completas
y verifiquen el estado final.

#### R-07 — `REBUILD` pierde el contenido del multiline

**Descripción**: cuando el usuario pulsa *Actualizar* (cambio de `NV`) o
carga un modelo RNA, la ventana se reconstruye. El multiline `res-OUTPUT-`
pierde el texto que contenía.

**Probabilidad**: alta. Ocurre cada vez que se cambia `NV` tras una
ejecución.

**Impacto**: bajo. Molesta, pero la información se puede volver a generar.

**Mitigación actual**: ninguna. La figura del canvas sí se conserva
(mediante `redibujar_resultados`), pero el texto no.

**Mitigación pendiente**: guardar el buffer de `OutputGUI` en `estado` y
restaurarlo en `_build_window`. Trabajo estimado: ~30 líneas.

#### R-08 — Bloqueo de la GUI por callback de progreso

**Descripción**: durante la ejecución del PSO, el callback `_on_iteracion`
llama a `window.refresh()` en cada iteración. Si una iteración tarda mucho
(por ejemplo, evaluación costosa del modelo RNA), la ventana puede parecer
congelada.

**Probabilidad**: baja en escenarios típicos. Media si el modelo RNA es
grande o `NP` es alto.

**Impacto**: bajo. No rompe nada, pero el usuario puede pensar que se colgó.

**Mitigación actual**: el callback envuelve la actualización en `try/except`
para no abortar el PSO si la UI falla.

**Mitigación pendiente**: si surge el problema en la práctica, mover el
cómputo a un hilo separado con `threading` y comunicar el progreso a la GUI
mediante una cola. Trabajo estimado: ~100 líneas. **No abordar hasta que se
observe el problema real**.

#### R-09 — Partículas fuera del dominio de `log` / `sqrt`

**Descripción**: si la función objetivo contiene `log` o `sqrt`, y una
partícula del enjambre cae fuera del dominio, la evaluación lanza
`ValueError` y el PSO se detiene.

**Probabilidad**: media. Depende de los límites y de la función elegida.

**Impacto**: alto. La ejecución se aborta sin resultados parciales
reutilizables.

**Mitigación actual**: se captura el `ValueError` y se muestra un popup
explicativo al usuario. El usuario debe ajustar los límites.

**Mitigación pendiente**: opcionalmente, penalizar con un valor muy alto
(para minimización) o muy bajo (para maximización) en lugar de abortar.
Esto permitiría al enjambre "aprender" a evitar la zona prohibida. Requiere
una discusión sobre si vale la pena complicar la semántica.

#### R-10 — Extrapolación del modelo RNA fuera del rango entrenado

**Descripción**: si el modelo RNA se entrenó con `lim_inf` / `lim_sup`
concretos, y el usuario configura el PSO con límites más amplios, las
predicciones del modelo fuera del rango son arbitrarias (el `StandardScaler`
no cubre esos valores).

**Probabilidad**: media. El usuario debe ser consciente del rango del
entrenamiento.

**Impacto**: alto. El PSO optimiza sobre una superficie que no refleja la
realidad.

**Mitigación actual**: al cargar un modelo, el tab PSO autorellena los
límites desde el `config.json`. Si el usuario los modifica manualmente, el
sistema no lo advierte.

**Mitigación pendiente**: añadir una advertencia visible en el panel
`pso-INFO_RNA-` cuando los límites del formulario difieran de los del
modelo.

### 3.3 Riesgos de uso

#### R-11 — Límites incoherentes

**Descripción**: el usuario introduce `lim_inf[i] ≥ lim_sup[i]` por error
de tecleo o incomprensión.

**Probabilidad**: alta.

**Impacto**: bajo. Se detecta en la validación antes de ejecutar.

**Mitigación actual**: validación previa; se muestra popup con el índice de
la variable conflictiva.

**Mitigación pendiente**: ninguna. Es suficiente.

#### R-12 — `config.json` corrupto o de versión desconocida

**Descripción**: el usuario carga una carpeta cuyo `config.json` está
editado a mano, es de una versión futura o ha sido reemplazado por otro
archivo.

**Probabilidad**: baja.

**Impacto**: medio. La carga falla con popup, pero no rompe el estado.

**Mitigación actual**: `Hibrido` verifica existencia y validez JSON; si
falla, popup con el error. No hay validación de `version` todavía.

**Mitigación pendiente**: validar el campo `version` y rechazar versiones
desconocidas con un mensaje claro.

**Mitigación adicional (2026-10-02)**: `buscador_modelos` valida que el
`config.json` tenga `tipo: "RNA"` y que existan los tres archivos
auxiliares antes de listar un modelo. Los modelos incompletos se ignoran
con warning en el log.

#### R-13 — Exportación a carpeta sin permisos

**Descripción**: el usuario elige una carpeta donde no tiene permiso de
escritura (por ejemplo, `C:\Program Files` en Windows sin elevación).

**Probabilidad**: media.

**Impacto**: bajo. La exportación falla con popup; no se corrompe nada.

**Mitigación actual**: `try/except` alrededor de la escritura; popup con el
mensaje de la excepción.

**Mitigación pendiente**: ninguna. El usuario debe elegir una carpeta
adecuada.

#### R-14 — `NI` muy alto sin parada temprana

**Descripción**: el usuario configura `NI = 10000` sin activar parada
temprana. El PSO itera sin mejorar durante miles de iteraciones.

**Probabilidad**: media.

**Impacto**: bajo. No rompe nada, pero desperdicia tiempo del usuario.

**Mitigación actual**: el panel de progreso permite ver que se está
ejecutando. La parada temprana está disponible como opción.

**Mitigación pendiente**: opcionalmente, sugerir valores por defecto de
`RONDAS` y `TOL` al marcar parada temprana. No crítico.

#### R-15 — RNA entrenada con muy pocas muestras

**Descripción**: el usuario entrena la RNA con 20 muestras para una función
compleja. El modelo generaliza mal; los resultados del PSO son ruido.

**Probabilidad**: media.

**Impacto**: medio. Los resultados parecen plausibles pero son incorrectos.

**Mitigación actual**: ninguna. El usuario no recibe advertencia.

**Mitigación pendiente**: en `CONSTRAINTS.md` (sección 2.4) se documentan
las recomendaciones. Podría añadirse una advertencia visual cuando
`muestras < 100`.

### 3.4 Riesgos de mantenimiento

#### R-16 — Ausencia de tests automáticos

**Descripción**: sin tests, cualquier refactor puede romper funcionalidad
sin que se note hasta que un usuario lo reporte.

**Probabilidad**: alta. Ya está ocurriendo en cada cambio.

**Impacto**: medio-alto. Afecta a la velocidad de desarrollo y a la
confianza en los cambios.

**Mitigación actual**: suite de 39 tests con `pytest` cubriendo
`funcion_objetivo.py`, `Particula_M.py` y `Enjambre_M.py`. Ejecutable con
`pytest` (o `pytest -m "not slow"` para excluir los tests del enjambre).

**Mitigación pendiente**: punto 7 del roadmap. Escribir tests con `pytest`
para `funcion_objetivo.py`, `Hibrido.py` y el enjambre con semilla fija.

#### R-17 — Ausencia de logging persistente

**Descripción**: los mensajes de ejecución se redirigen al multiline de la
GUI, pero se pierden al cerrar la aplicación. No hay archivo de log para
diagnóstico post-mortem.

**Probabilidad**: alta.

**Impacto**: medio. Dificulta investigar bugs reportados por terceros.

**Mitigación actual**: logging estructurado con doble salida (archivo por
operación en `resultados_pso/logs/` + GUI). Configuración externa en
`logging_config.json` con fallback silencioso. Formato con timestamp,
nivel y módulo emisor.

**Mitigación pendiente**: punto 8 del roadmap. Configurar `logging` con
handler a archivo en `resultados_pso/run_YYYYMMDD_HHMMSS.log`.

#### R-18 — Falta de migración de `config.json`

**Descripción**: cuando el formato de `config.json` cambie (por ejemplo, al
añadir `origen` en el punto 5 del roadmap), los modelos exportados con la
versión anterior pueden fallar al cargarse.

**Probabilidad**: media. El formato actual es `version: 1`.

**Impacto**: medio. Modelos viejos dejan de ser usables.

**Mitigación actual**: el campo `version` ya existe en el formato, pero no
se valida.

**Mitigación pendiente**: implementar en `Hibrido.cargar_funcion_prediccion`
un despachador que lea `version` y decida cómo interpretar el resto del
JSON. Se hace cuando aparezca la versión 2.

#### R-19 — Acoplamiento RNA → PSO sin contrato explícito

**Descripción**: el acoplamiento entre el tab RNA y el tab PSO se hace a
través del formato de `config.json`, pero no hay un esquema formal que
valide los campos obligatorios. Un `config.json` con campos faltantes
produce errores en tiempo de carga, no en tiempo de exportación.

**Probabilidad**: media.

**Impacto**: bajo. Se detecta al cargar y se puede corregir.

**Mitigación actual**: `Hibrido` verifica la existencia de los 4 archivos
y lee el JSON, pero no valida campos específicos.

**Mitigación pendiente**: definir un esquema (p. ej. `jsonschema`) y
validar al exportar y al cargar.

#### R-20 — Incompatibilidad de PySimpleGUI entre versiones

**Descripción**: PySimpleGUI ha evolucionado entre las ramas 4.x y 5.x con
cambios en la resolución de claves y la reutilización de widgets. Un layout
que funciona en 4.x puede fallar en 5.x con errores como
`PROMPTING TO REUSE AN ELEMENT` o `The closest matching key`, especialmente
cuando dos claves comparten un prefijo ambiguo (por ejemplo
`res-HISTORIAL-` y `res-HIST-CONT-`).

**Probabilidad**: alta si el proyecto se distribuye a terceros que instalan
su propia versión de PySimpleGUI.

**Impacto**: medio. Un layout que funciona en la máquina del desarrollador
puede fallar en la del usuario sin cambios aparentes en el código.

**Mitigación actual**:

- El proyecto usa claves con prefijos únicos y sin guiones internos
  después del prefijo (`res-HISTTABLA-`, no `res-HIST-TABLA-`).
- `pyrightconfig.json` en la raíz relaja los diagnósticos de Pylance
  para que los falsos positivos no oculten errores reales.
- Se prueba la app en dos máquinas con versiones distintas de
  PySimpleGUI antes de fusionar a `main`.

**Mitigación pendiente**:

- Fijar la versión de PySimpleGUI en `requirements.txt` a una rama
  específica (`PySimpleGUI>=4.60,<5.0`).
- Documentar la versión mínima en `CONSTRAINTS.md`, sección 6.1.
- Reevaluar la migración a `FreeSimpleGUI` (ver R-01), que mantiene
  una sola rama activa y elimina este problema de raíz.

#### R-21 — Reentrenamiento imposible sin los datos originales

**Descripción**: el bloque `origen` del `config.json` guarda la arquitectura
y los parámetros de entrenamiento, pero **no los datos de entrada**. Si el
modelo se entrenó con un CSV importado y ese archivo se pierde, el usuario
puede precargar la arquitectura pero no puede regenerar los datos
automáticamente.

**Probabilidad**: media. Ocurre cuando se comparten modelos entre máquinas
o cuando el CSV original se mueve/borra.

**Impacto**: bajo. La arquitectura sí se precarga; el usuario solo debe
volver a seleccionar el archivo de datos.

**Mitigación actual**:

- El botón "Reentrenar" solo se habilita si el modelo tiene bloque `origen`.
- Para modelos entrenados con datos importados, se muestra un popup
  informativo explicando que hay que recargar el archivo de datos.

**Mitigación pendiente**:

- Opcionalmente, guardar una copia reducida del CSV (primeras N filas) en
  la carpeta de exportación. Descartado por ahora: aumenta el tamaño del
  modelo y complica la exportación.

---

## 4. Matriz resumen

Vista condensada de los 19 riesgos. La columna **Estado** indica:

- **Mitigado**: hay una mitigación implementada y probada.
- **Parcial**: hay mitigación, pero con lagunas.
- **Sin mitigar**: riesgo identificado, sin acción actual.

| ID | Categoría | Prob. | Impacto | Estado |
|---|---|---|---|---|
| R-01 | Dependencia externa | Baja | Bajo | Mitigado |
| R-02 | Dependencia externa | Media | Medio | Parcial |
| R-03 | Dependencia externa | Media | Alto | Parcial |
| R-04 | Dependencia externa | Baja | Medio | Mitigado |
| R-05 | Dependencia externa | Media | Medio | Parcial |
| R-06 | Técnico interno | Media | Medio | Parcial |
| R-07 | Técnico interno | Alta | Bajo | Sin mitigar |
| R-08 | Técnico interno | Baja | Bajo | Parcial |
| R-09 | Técnico interno | Media | Alto | Parcial |
| R-10 | Técnico interno | Media | Alto | Parcial |
| R-11 | De uso | Alta | Bajo | Mitigado |
| R-12 | De uso | Baja | Medio | Parcial |
| R-13 | De uso | Media | Bajo | Mitigado |
| R-14 | De uso | Media | Bajo | Parcial |
| R-15 | De uso | Media | Medio | Sin mitigar |
| R-16 | Mantenimiento | Alta | Medio-alto | Parcial |
| R-17 | Mantenimiento | Alta | Medio | Mitigado |
| R-18 | Mantenimiento | Media | Medio | Parcial |
| R-19 | Mantenimiento | Media | Bajo | Parcial |
| R-20 | Dependencia externa | Alta | Medio | Parcial |
| R-21 | De uso | Media | Bajo | Parcial |

---

## 5. Riesgos aceptados (fuera de alcance)

Los siguientes riesgos se han considerado y **se decide no mitigar** por
razones de coste/beneficio o porque quedan fuera del alcance del proyecto:

- **Ataques de canal lateral**: no aplica a una aplicación local sin
  servicios de red.
- **Manipulación de los archivos generados entre sesiones**: se asume que
  el usuario no modifica `modelo.keras`, `scaler_x.save` ni `config.json`
  con intenciones maliciosas.
- **Ataques sobre el entorno de Python**: si un atacante puede inyectar
  módulos en `sys.path`, ya controla el sistema operativo.
- **Red**: la aplicación no abre puertos ni conexiones salientes. No hay
  superficie de red que proteger.
- **Modelos RNA con más de un target**: fuera de alcance. Si se requiere,
  será un proyecto distinto.
- **Optimización multi-objetivo**: el PSO implementado es mono-objetivo.
  Extenderlo a multi-objetivo (por ejemplo, NSGA-II) implicaría un motor
  nuevo.

---

## 6. Plan de mitigación priorizada

Los riesgos se ordenan por **coste de no mitigarlos** en el contexto actual
(proyecto en fase pre-evaluación, con distribución a terceros prevista).

| Prioridad | Riesgo | Mitigación prevista | Punto del roadmap |
|---|---|---|---|
| 1 | R-16 | Tests con `pytest` | Punto 7 ✅ |
| 2 | R-17 | Logging estructurado | Punto 8 ✅ |
| 3 | R-01 | Migrar a `FreeSimpleGUI` (rama dedicada) | Antes de distribución pública |
| 4 | R-04 | Verificación de Tk al arrancar + docs de requisitos | Con el empaquetado `.exe` |
| 5 | R-15 | Advertencia visual cuando `muestras < 100` | Con el punto 8 |
| 6 | R-07 | Persistir el buffer de `OutputGUI` en `estado` | Con el punto 6 |
| 7 | R-10 | Advertencia al modificar límites tras cargar modelo RNA | Con el punto 4 |
| 8 | R-12, R-18, R-19 | Validación de esquema JSON | Después del punto 5 |
| 9 | R-05 | Estrategia de empaquetado selectivo | Con el `.exe` |
| 10 | R-09 | Penalización en lugar de aborto | Fuera del roadmap actual |
| — | R-08 | Cómputo en hilo separado | Solo si se observa en la práctica |

---

## 7. Cómo actualizar este documento

Reglas para mantener `RISKS.md` útil a lo largo del tiempo:

1. **Añadir un riesgo nuevo**: asignar el siguiente `R-XX` disponible,
   incluirlo en su categoría y en la matriz resumen (sección 4).
2. **Mitigar un riesgo existente**: cambiar su estado en la matriz a
   *Mitigado* o *Parcial*, y referenciar el commit o el punto del roadmap
   que lo cubre.
3. **Revisar la matriz**: antes de cada release mayor (por ejemplo,
   `v1.0.0`) o cuando cambie el contexto de uso (nueva máquina, nuevo
   usuario, distribución pública).
4. **Retirar riesgos obsoletos**: si un riesgo deja de aplicar (por
   ejemplo, porque se abandona la dependencia que lo causaba), eliminar la
   entrada y dejar constancia en el commit.

### Historial de actualizaciones

- **2026-09-29**: R-16 pasa a mitigación parcial con la incorporación de
  tests automáticos (`feature/tests-pytest`).
- **2026-09-30**: R-17 pasa a mitigado con logging estructurado por
  operación (`feature/logging-estructurado`).
- **2026-10-02**: R-12 refuerza su mitigación con validación de esquema
  en el escáner de modelos (`feature/lista-modelos`).
- **2026-10-05**: R-20 añadido tras detectar colisión de claves entre
  PySimpleGUI 4.x y 5.x en la máquina secundaria.
- **2026-10-05**: R-01 reformulada (licencia resuelta con LGPL3, pero
  desarrollo limitado). R-22 añadida para seguimiento de FreeSimpleGUI.
- **2026-10-06**: R-01 y R-22 mitigados con la migración a FreeSimpleGUI.
- **2026-10-07**: R-04 y R-05 mitigados parcialmente con el empaquetado
  PyInstaller (`feature/empaquetado-exe`).

Sin estas reglas, el documento envejece y pasa a ser una foto del pasado
en lugar de una guía viva.