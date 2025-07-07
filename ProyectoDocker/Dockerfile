FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install requests numpy cython

COPY algoritmos/ ./algoritmos/
COPY run_esclavo.py .

# Compila el módulo Cython
WORKDIR /app/algoritmos
COPY algoritmos/setup.py .
RUN python3 setup.py build_ext --inplace

WORKDIR /app

ENTRYPOINT ["python", "run_esclavo.py"]