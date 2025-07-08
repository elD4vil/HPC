FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias básicas
RUN pip install flask requests psutil numpy cython

# Copiar archivos del esclavo (desde el directorio padre)
COPY esclavo_api.py .
COPY algoritmos/ ./algoritmos/

# Compilar el módulo Cython
WORKDIR /app/algoritmos
RUN python3 setup.py build_ext --inplace

WORKDIR /app

EXPOSE 5002

CMD ["python", "esclavo_api.py"]
