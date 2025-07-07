import subprocess
import sys
import time
import requests  
import socket
import os


# Recibe: algoritmo width height iteraciones
algoritmo = sys.argv[1]
width = sys.argv[2]
height = sys.argv[3]
iteraciones = sys.argv[4]

start_time = time.time()
subprocess.run(["python", f"algoritmos/{algoritmo}.py", width, height, iteraciones])
end_time = time.time()

tiempo = round(end_time - start_time, 3)
esclavo_nombre = os.getenv("ESCLAVO", socket.gethostname())

# Preparar el resultado
resultado = {
    "esclavo": esclavo_nombre,
    "algoritmo": algoritmo,
    "resolucion": f"{width}x{height}",
    "iteraciones": iteraciones,
    "tiempo": tiempo
}

print(f"[{esclavo_nombre}] Resultado: {resultado}")

# Enviar al maestro (ajusta la IP si es necesario)
try:
    requests.post("http://192.168.56.1:5001/resultado", json=resultado)
except Exception as e:
    print("Error al enviar resultado al maestro:", e)
