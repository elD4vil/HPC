import matplotlib.pyplot as plt
import time
import sys

# Obtener parámetros desde la línea de comandos
# Uso: python Secuencial.py [width] [height] [max_iter]
width = int(sys.argv[1]) if len(sys.argv) > 1 else 800
height = int(sys.argv[2]) if len(sys.argv) > 2 else 800
max_iter = int(sys.argv[3]) if len(sys.argv) > 3 else 1100

zoom = 1
move_x, move_y = 0.0, 0.0
c = complex(0, 0)

# Crear grilla
x_min, x_max = -1.5 * zoom + move_x, 1.5 * zoom + move_x
y_min, y_max = -1.5 * zoom + move_y, 1.5 * zoom + move_y

# Inicializar matriz de resultados
iteration_counts = [[0 for _ in range(width)] for _ in range(height)]

start_time = time.time()

for j in range(height):
    y = y_min + (y_max - y_min) * j / (height - 1)
    for i in range(width):
        x = x_min + (x_max - x_min) * i / (width - 1)
        z = complex(x, y)
        count = 0
        while abs(z) <= 2 and count < max_iter:
            z = z * z + c
            count += 1
        iteration_counts[j][i] = count

end_time = time.time()

print(f"[Secuencial] Tiempo de procesamiento: {end_time - start_time:.3f} segundos")

# Guardar imagen con nombre según parámetros
plt.figure(figsize=(8, 8))
plt.imshow(iteration_counts, cmap="inferno", extent=(-1.5, 1.5, -1.5, 1.5))
plt.axis("off")
plt.savefig(f"salida_secuencial_{width}x{height}_{max_iter}.png")
