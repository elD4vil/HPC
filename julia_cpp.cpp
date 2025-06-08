#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>

namespace py = pybind11;

py::array_t<int> julia_set_cpp(int width, int height, double x_min, double x_max, double y_min, double y_max,
                               double creal, double cimag, int max_iter) {
    auto result = py::array_t<int>({height, width});
    auto buf = result.mutable_unchecked<2>();

    for (int j = 0; j < height; ++j) {
        double y = y_min + (y_max - y_min) * j / (height - 1);
        for (int i = 0; i < width; ++i) {
            double x = x_min + (x_max - x_min) * i / (width - 1);
            double zx = x, zy = y;
            int k = 0;
            while (zx*zx + zy*zy <= 4.0 && k < max_iter) {
                double tmp = zx*zx - zy*zy + creal;
                zy = 2.0*zx*zy + cimag;
                zx = tmp;
                ++k;
            }
            buf(j, i) = k;
        }
    }
    return result;
}

PYBIND11_MODULE(julia_cpp, m) {
    m.def("julia_set_cpp", &julia_set_cpp, "Calculo del conjunto de Julia en C++");
}