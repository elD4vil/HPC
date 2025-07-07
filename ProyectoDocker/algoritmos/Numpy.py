import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Parámetros desde terminal
width = int(sys.argv[1]) if len(sys.argv) > 1 else 800
height = int(sys.argv[2]) if len(sys.argv) > 2 else 800
max_iter = int(sys.argv[3]) if len(sys.argv) > 3 else 300

zoom = 1
move_x, move_y = 0.0, 0.0
c = complex(0, 0)

x = np.linspace(-1.5, 1.5, width) * zoom + move_x
y = np.linspace(-1.5, 1.5, height) * zoom + move_y
X, Y = np.meshgrid(x, y)
Z = X + 1j * Y

def julia_row(row_idx):
    z_row = Z[row_idx].copy()
    count_row = np.zeros(z_row.shape, dtype=int)
    mask_row = np.full(z_row.shape, True, dtype=bool)
    for i in range(max_iter):
        z_row[mask_row] = z_row[mask_row]**2 + c
        mask_row = np.abs(z_row) <= 2
        count_row += mask_row
        if not mask_row.any():
            break
    return count_row

start_time_parallel = time.time()

with ThreadPoolExecutor() as executor:
    results = list(executor.map(julia_row, range(height)))

iteration_counts_parallel = np.array(results)

end_time_parallel = time.time()
print(f"[Paralelo] Tiempo de procesamiento: {end_time_parallel - start_time_parallel:.3f} segundos")

plt.figure(figsize=(8, 8))
plt.imshow(iteration_counts_parallel, cmap="inferno", extent=(-1.5, 1.5, -1.5, 1.5))
plt.axis("off")
plt.savefig(f"salida_numpy_{width}x{height}_{max_iter}.png")