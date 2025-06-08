import numpy as np
import matplotlib.pyplot as plt
import time
from julia_cython import julia_set

width, height = 800, 800
zoom = 1
move_x, move_y = 0.0, 0.0
max_iter = 1100
c = complex(0, 0)

x_min, x_max = -1.5 * zoom + move_x, 1.5 * zoom + move_x
y_min, y_max = -1.5 * zoom + move_y, 1.5 * zoom + move_y

start_time = time.time()
iteration_counts = julia_set(width, height, x_min, x_max, y_min, y_max, c.real, c.imag, max_iter)
end_time = time.time()
print(f"Tiempo de procesamiento: {end_time - start_time:.3f} segundos")

plt.figure(figsize=(8, 8))
plt.imshow(iteration_counts, cmap="inferno", extent=(x_min, x_max, y_min, y_max))
plt.title(f"Conjunto de Julia para c = {c}")
plt.axis("off")
plt.show()