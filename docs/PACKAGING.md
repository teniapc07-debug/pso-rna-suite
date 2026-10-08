# Empaquetado del proyecto

> Cómo generar el ejecutable portable de la suite PSO + RNA para Windows.

---

## 1. Requisitos previos

- Python 3.13 (gestionado por `uv`).
- Entorno virtual sincronizado: `uv sync`.
- Microsoft Visual C++ Redistributable 2015-2022 (x64) instalado en la
  máquina que compila. Ver R-23 en `RISKS.md`.

---

## 2. Herramienta

Se usa **PyInstaller** en modo **`--onedir`** (carpeta autocontenida).

### ¿Por qué no `--onefile`?

- Con TensorFlow, el modo `--onefile` descomprime cientos de MB en un
  directorio temporal en cada arranque, con tiempos de inicio > 10 s.
- Tkinter/Tcl encuentra las librerías de forma más fiable en modo
  `--onedir`.
- La depuración es más simple: se ve exactamente qué archivos se incluyen.

---

## 3. Archivos implicados

| Archivo | Rol |
|---|---|
| `PSO_RNA_Suite.spec` | Configuración de PyInstaller, versionada en Git |
| `PSO_RNA_Suite.ico` | Icono del ejecutable (opcional) |
| `app.py` | Punto de entrada de la aplicación |
| `logica/rutas.py` | Centraliza las rutas de datos (cwd o home) |

---

## 4. Proceso de compilación

Desde la raíz del proyecto:

```bash
uv run pyinstaller PSO_RNA_Suite.spec --noconfirm
```

**Tiempo estimado**: 3-10 minutos la primera vez, menos en recompilaciones
incrementales.

**Salida**:

```
dist/
└── PSO_RNA_Suite/
    ├── PSO_RNA_Suite.exe     ← ejecutable
    └── _internal/            ← dependencias (~800 MB - 1.5 GB)
```

---

## 5. Verificación

Ejecutar el `.exe` y comprobar el flujo completo: cargar modelo, ejecutar
PSO, guardar gráfica, exportar historial.

Si el `.exe` no arranca, ejecutarlo desde una consola:

```cmd
cd dist\PSO_RNA_Suite
PSO_RNA_Suite.exe
```

Los errores de arranque se imprimen en la consola aunque la app no muestre
ventana propia.

---

## 6. Rutas de datos en el ejecutable

En modo desarrollo (ejecutando desde el repo), los archivos generados
(`resultados_pso/`, `exportaciones/`, logs) se escriben en el `cwd`.

En modo empaquetado, `logica/rutas.py` redirige todo a:

```
%USERPROFILE%\PSO_RNA_Suite\
├── resultados_pso/
│   ├── Historial_Enjambre.csv
│   ├── grafica_enjambre.png
│   └── logs/
├── exportaciones/
└── historial_ejecuciones.json
```

Esto evita problemas de permisos cuando el `.exe` se ejecuta desde
ubicaciones como `C:\Program Files`.

---

## 7. Distribución

Distribuir **la carpeta completa** `dist/PSO_RNA_Suite/`:

- Comprimirla en un `.zip`.
- El usuario descomprime y ejecuta `PSO_RNA_Suite.exe`.
- No es necesario instalar Python.

**Tamaño típico del `.zip`**: 400-700 MB (comprimido).

---

## 8. Notas de mantenimiento

- Si se añade una nueva dependencia, revisar si requiere un nuevo
  `hiddenimport` o `collect_data_files` en el `.spec`.
- Si el `.exe` falla con `ModuleNotFoundError`, añadir el módulo a
  `hiddenimports` y recompilar.
- Para regenerar el icono, ver la sección correspondiente en el README.