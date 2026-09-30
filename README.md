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