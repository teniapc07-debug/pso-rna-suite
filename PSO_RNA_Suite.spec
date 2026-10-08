# PSO_RNA_Suite.spec
# Configuración de PyInstaller para empaquetar la Suite PSO + RNA.
# Modo: --onedir (carpeta autocontenida).

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# --- Dependencias ocultas que PyInstaller no detecta automáticamente ---
hiddenimports = [
    # TensorFlow
    'tensorflow',
    'tensorflow.python',
    'tensorflow.python.platform',
    'keras',
    # sklearn
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.utils._heap',
    'sklearn.utils._sorting',
    'sklearn.utils._vector_sentinel',
    'sklearn.neighbors._partition_nodes',
    # pandas / openpyxl
    'openpyxl',
    'pandas',
    # matplotlib
    'matplotlib.backends.backend_tkagg',
    # FreeSimpleGUI
    'FreeSimpleGUI',
    # joblib
    'joblib',
]

# --- Datos que hay que copiar (no solo código Python) ---
datas = []
datas += collect_data_files('tensorflow')
datas += collect_data_files('keras')
datas += collect_data_files('sklearn')
datas += collect_data_files('matplotlib')

# --- Configuración ---
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'test',
        'doctest',
        # Excluir backends de matplotlib que no usamos
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_webagg',
        # Excluir Jupyter
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PSO_RNA_Suite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX a veces rompe TF
    console=False,      # sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PSO_RNA_Suite',
)