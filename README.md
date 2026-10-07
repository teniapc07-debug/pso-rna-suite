# Suite PSO + RNA

Aplicación de escritorio con **dos módulos intercambiables** en una sola ventana:

1. **Optimizador PSO** — Particle Swarm Optimization multi-variable sobre una
   función objetivo simbólica *o* sobre un modelo de red neuronal previamente
   entrenado.
2. **Constructor RNA** — Diseño, entrenamiento, validación y exportación de
   Redes Neuronales Artificiales (Keras/TensorFlow).

Ambos módulos comparten estado en memoria, de modo que puedes **entrenar una RNA
y usarla inmediatamente como función objetivo del PSO** sin reiniciar la app.

---

## 1. Requisitos

- Python 3.10 o superior
- Sistema operativo: Windows / Linux / macOS (con backend Tk para Matplotlib)

### Dependencias

```bash
pip install PySimpleGUI tensorflow scikit-learn joblib matplotlib pandas numpy

## Documentación

| Documento | Contenido |
|---|---|
| [README.md](README.md) | Instalación, uso básico, dependencias |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Estructura estática del proyecto |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | Flujos operativos paso a paso |
| [docs/CONSTRAINTS.md](docs/CONSTRAINTS.md) | Reglas, dominios, invariantes |
| [docs/RISKS.md](docs/RISKS.md) | Riesgos, matriz y plan de mitigación |

## Tests

La suite incluye **52 pruebas automáticas** con `pytest` que cubren el
parser de funciones objetivo, la clase `partícula`, el motor del enjambre,
el módulo de logging y el historial de ejecuciones.

## Compilación del ejecutable

El proyecto se puede empaquetar como aplicación de escritorio autónoma
con PyInstaller.

### Requisitos

- PyInstaller instalado (`uv sync --all-extras`).
- ~2 GB de espacio libre en disco para la build.

### Compilar

```bash
uv run pyinstaller psov2.spec --clean --noconfirm
```

El resultado se genera en `dist/psov2/`. La carpeta completa pesa
aproximadamente **1.3 GB** (TensorFlow incluido) y puede comprimirse
en ZIP para su distribución.

### Probar en limpio

Copia `dist/psov2/` a otra ubicación (por ejemplo, el Escritorio) y
ejecuta `psov2.exe` desde allí. La primera ejecución crea las carpetas
`resultados_pso/` y `exportaciones/` **junto al ejecutable**, no dentro
del bundle.

### Notas

- El `.spec` incluye los hidden imports necesarios para TensorFlow y
  Keras. Si actualizas TensorFlow a una versión mayor, puede que haya
  que añadir más módulos a `hiddenimports`.
- Para reducir tamaño, considera dividir la suite en dos ejecutables
  (uno ligero sin TensorFlow, otro pesado).

### Instalación de dependencias de desarrollo

```bash
pip install -r requirements-dev.txt
```

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar solo los tests rápidos

Los tests del enjambre están marcados con `@pytest.mark.slow`. Para
excluirlos durante el desarrollo:

```bash
pytest -m "not slow"
```

### Medir cobertura

```bash
pytest --cov=PSO_MV --cov=RNA --cov=logica --cov-report=term-missing
```

### Estructura de `tests/`

| Archivo | Cobertura |
|---|---|
| `test_funcion_objetivo.py` | Parser AST, dominios, nodos prohibidos |
| `test_particula.py` | Inicialización, evaluación, límites |
| `test_enjambre.py` | Convergencia, parada temprana, historial |
| `test_logging_config.py` | Configuración, operaciones, GUIHandler |
| `test_historial.py` | Persistencia, cap de 200, corrupción |