import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
def julia_set(int width, int height, double x_min, double x_max, double y_min, double y_max, 
              double creal, double cimag, int max_iter):
    cdef np.ndarray[np.int32_t, ndim=2] counts = np.zeros((height, width), dtype=np.int32)
    cdef int i, j, k
    cdef double x, y, zx, zy, zx2, zy2, tmp
    for j in range(height):
        y = y_min + (y_max - y_min) * j / (height - 1)
        for i in range(width):
            x = x_min + (x_max - x_min) * i / (width - 1)
            zx, zy = x, y
            k = 0
            while zx*zx + zy*zy <= 4.0 and k < max_iter:
                tmp = zx*zx - zy*zy + creal
                zy = 2.0*zx*zy + cimag
                zx = tmp
                k += 1
            counts[j, i] = k
    return counts