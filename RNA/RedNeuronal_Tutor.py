import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

# ==========================================
# 1. DATOS SINTÉTICOS SIMPLES (y = x²)
# ==========================================
# Generamos 2000 números aleatorios entre -10 y 10
X_train = np.random.uniform(-10, 10, (2000, 1))
# Calculamos su valor sintético real usando la matemática pura
y_train = X_train ** 2

# ==========================================
# 2. UNA RED NEURONAL PEQUEÑA
# ==========================================
model = models.Sequential([
    layers.Input(shape=(1,)), # Recibe 1 solo número (X)
    layers.Dense(64, activation='relu'), # Capas ocultas para aprender la curva
    layers.Dense(32, activation='relu'),
    layers.Dense(1) # Devuelve 1 solo número de salida (Y)
])

model.compile(optimizer='adam', loss='mse')
# Entrenamos rápido (solo 15 épocas para esta prueba rápida)
model.fit(X_train, y_train, epochs=15, batch_size=32, verbose=0)

# ==========================================
# 3. EL EJEMPLO INTERACTIVO (Tu duda)
# ==========================================
print("--- ¡RED ENTRENADA CON ÉXITO! ---")
print("Vamos a comprobar qué tanto aprendió la IA sobre la función y = x²")

# Simulamos que tú ingresas el número 3
numero_usuario = float(input("Ingresa un número para que la IA prediga su cuadrado: "))

# 1. Calculamos el valor sintético impuesto (La matemática exacta)
valor_matematico_real = numero_usuario ** 2

# 2. Le pedimos a TensorFlow su predicción (Requiere formato de matriz [[3.0]])
datos_para_ia = np.array([[numero_usuario]])
prediccion_ia = model.predict(datos_para_ia, verbose=0)[0][0]

# 3. Comparamos los dos resultados cara a cara
print(f"\nNúmero ingresado: {numero_usuario}")
print(f"🧮 Valor Real Matemático:   {valor_matematico_real}")
print(f"🤖 Predicción de la IA:      {prediccion_ia:.4f}")

# Calculamos el error final
error = abs(valor_matematico_real - prediccion_ia)
print(f"⚠️ Error de la IA:           {error:.4f}")
