import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from julia_cython import julia_set

# Parámetros desde terminal
width = int(sys.argv[1]) if len(sys.argv) > 1 else 800
height = int(sys.argv[2]) if len(sys.argv) > 2 else 800
max_iter = int(sys.argv[3]) if len(sys.argv) > 3 else 1100

zoom = 1
move_x, move_y = 0.0, 0.0
c = complex(0, 0)

x_min, x_max = -1.5 * zoom + move_x, 1.5 * zoom + move_x
y_min, y_max = -1.5 * zoom + move_y, 1.5 * zoom + move_y

start_time = time.time()
iteration_counts = julia_set(width, height, x_min, x_max, y_min, y_max, c.real, c.imag, max_iter)
end_time = time.time()
print(f"Tiempo de procesamiento: {end_time - start_time:.3f} segundos")

plt.figure(figsize=(8, 8))
plt.imshow(iteration_counts, cmap="inferno", extent=(x_min, x_max, y_min, y_max))
plt.axis("off")
plt.savefig(f"salida_cython_{width}x{height}_{max_iter}.png")