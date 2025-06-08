import matplotlib.pyplot as plt
import time

width, height = 800, 800
zoom = 1
move_x, move_y = 0.0, 0.0
max_iter = 1100
c = complex(0, 0)

# Crear la grilla de puntos complejos de forma secuencial
x_min, x_max = -1.5 * zoom + move_x, 1.5 * zoom + move_x
y_min, y_max = -1.5 * zoom + move_y, 1.5 * zoom + move_y

# Inicializar la matriz de resultados
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
print(f"Tiempo de procesamiento: {end_time - start_time:.3f} segundos")

plt.figure(figsize=(8, 8))
plt.imshow(iteration_counts, cmap="inferno", extent=(-1.5, 1.5, -1.5, 1.5))
plt.title(f"Conjunto de Julia para c = {c}")
plt.axis("off")
plt.show()