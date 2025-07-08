from flask import Flask, request, jsonify
import subprocess
import time
import requests  
import socket
import os
import psutil
import threading

app = Flask(__name__)

# Configuración desde variables de entorno
ESCLAVO_HOST = os.getenv("ESCLAVO_HOST", "0.0.0.0")
ESCLAVO_PORT = int(os.getenv("ESCLAVO_PORT", "5002"))
MAESTRO_IP = os.getenv("MAESTRO_IP", "maestro")
MAESTRO_PORT = int(os.getenv("MAESTRO_PORT", "5001"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))
TIMEOUT_ALGORITMO = int(os.getenv("TIMEOUT_ALGORITMO", "300"))
ESCLAVO_TIMEOUT = int(os.getenv("ESCLAVO_TIMEOUT", "30"))
PING_TIMEOUT = int(os.getenv("PING_TIMEOUT", "5"))
MAX_REINTENTOS = int(os.getenv("MAX_REINTENTOS", "3"))
REINTENTO_DELAY = int(os.getenv("REINTENTO_DELAY", "5"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ALGORITMOS_DISPONIBLES = os.getenv("ALGORITMOS_DISPONIBLES", "Secuencial,Numpy,juliaCython").split(",")

# Estado del esclavo
estado_esclavo = {
    'ocupado': False,
    'trabajo_actual': None,
    'ultimo_trabajo': None
}

def obtener_info_sistema():
    """Obtiene información del sistema del esclavo"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memoria_libre': psutil.virtual_memory().available / (1024 * 1024),  # MB
        'memoria_total': psutil.virtual_memory().total / (1024 * 1024),  # MB
        'memoria_usada': psutil.virtual_memory().used / (1024 * 1024)  # MB
    }

def registrar_con_maestro():
    """Registra este esclavo con el maestro con reintentos"""
    esclavo_id = os.getenv("ESCLAVO", socket.gethostname())
    ip_esclavo = socket.gethostbyname(socket.gethostname())
    
    datos_registro = {
        'esclavo_id': esclavo_id,
        'ip': ip_esclavo,
        'puerto': ESCLAVO_PORT
    }
    
    for intento in range(MAX_REINTENTOS):
        try:
            print(f"[{esclavo_id}] Intento de registro {intento + 1}/{MAX_REINTENTOS}")
            response = requests.post(f"http://{MAESTRO_IP}:{MAESTRO_PORT}/registrar_esclavo", 
                                   json=datos_registro, timeout=HTTP_TIMEOUT)
            if response.status_code == 200:
                print(f"[{esclavo_id}] Registrado exitosamente con el maestro")
                return True
            else:
                print(f"[{esclavo_id}] Error al registrarse con el maestro: {response.status_code}")
        except Exception as e:
            print(f"[{esclavo_id}] Error al conectar con el maestro (intento {intento + 1}): {e}")
        
        if intento < MAX_REINTENTOS - 1:
            print(f"[{esclavo_id}] Reintentando en {REINTENTO_DELAY} segundos...")
            time.sleep(REINTENTO_DELAY)
    
    print(f"[{esclavo_id}] No se pudo registrar con el maestro después de {MAX_REINTENTOS} intentos")
    return False

@app.route("/ping", methods=["GET"])
def ping():
    """Responde al ping del maestro con información del sistema"""
    info_sistema = obtener_info_sistema()
    
    return jsonify({
        "status": "active",
        "timestamp": time.time(),
        "ocupado": estado_esclavo['ocupado'],
        "trabajo_actual": estado_esclavo['trabajo_actual'],
        **info_sistema
    })

@app.route("/ejecutar", methods=["POST"])
def ejecutar_trabajo():
    """Ejecuta un trabajo asignado por el maestro"""
    if estado_esclavo['ocupado']:
        return jsonify({
            "error": "Esclavo ocupado",
            "trabajo_actual": estado_esclavo['trabajo_actual']
        }), 409
    
    data = request.get_json()
    
    # Marcar como ocupado
    estado_esclavo['ocupado'] = True
    estado_esclavo['trabajo_actual'] = data
    
    # Ejecutar trabajo en un hilo separado
    thread = threading.Thread(target=procesar_trabajo, args=(data,))
    thread.start()
    
    return jsonify({
        "status": "accepted",
        "trabajo_id": data.get('id', 'unknown')
    }), 200

def procesar_trabajo(data):
    """Procesa un trabajo en background"""
    esclavo_nombre = os.getenv("ESCLAVO", socket.gethostname())
    
    try:
        algoritmo = data['algoritmo']
        
        # Validar que el algoritmo esté disponible
        if algoritmo not in ALGORITMOS_DISPONIBLES:
            raise ValueError(f"Algoritmo '{algoritmo}' no disponible. Algoritmos soportados: {ALGORITMOS_DISPONIBLES}")
        
        width = str(data['width'])
        height = str(data['height'])
        iteraciones = str(data['iteraciones'])
        
        print(f"[{esclavo_nombre}] Iniciando trabajo: {algoritmo} {width}x{height} {iteraciones} iteraciones")
        
        start_time = time.time()
        result = subprocess.run(["python", f"algoritmos/{algoritmo}.py", width, height, iteraciones], 
                              capture_output=True, text=True, timeout=TIMEOUT_ALGORITMO)
        end_time = time.time()
        
        tiempo = round(end_time - start_time, 3)
        
        # Preparar el resultado
        resultado = {
            "esclavo": esclavo_nombre,
            "algoritmo": algoritmo,
            "resolucion": f"{width}x{height}",
            "iteraciones": iteraciones,
            "tiempo": tiempo,
            "trabajo_id": data.get('id', 'unknown'),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
        print(f"[{esclavo_nombre}] Trabajo completado en {tiempo}s")
        
        # Enviar resultado al maestro
        try:
            requests.post(f"http://{MAESTRO_IP}:{MAESTRO_PORT}/resultado", 
                         json=resultado, timeout=HTTP_TIMEOUT)
            print(f"[{esclavo_nombre}] Resultado enviado al maestro")
        except Exception as e:
            print(f"[{esclavo_nombre}] Error al enviar resultado al maestro: {e}")
        
        # Actualizar estado
        estado_esclavo['ultimo_trabajo'] = resultado
        
    except subprocess.TimeoutExpired:
        print(f"[{esclavo_nombre}] Trabajo timeout después de {TIMEOUT_ALGORITMO}s")
        error_resultado = {
            "esclavo": esclavo_nombre,
            "trabajo_id": data.get('id', 'unknown'),
            "error": f"Timeout después de {TIMEOUT_ALGORITMO} segundos",
            "timestamp": time.time()
        }
        
        try:
            requests.post(f"http://{MAESTRO_IP}:{MAESTRO_PORT}/resultado", 
                         json=error_resultado, timeout=HTTP_TIMEOUT)
        except:
            pass
            
    except Exception as e:
        print(f"[{esclavo_nombre}] Error al procesar trabajo: {e}")
        
        # Enviar error al maestro
        error_resultado = {
            "esclavo": esclavo_nombre,
            "trabajo_id": data.get('id', 'unknown'),
            "error": str(e),
            "timestamp": time.time()
        }
        
        try:
            requests.post(f"http://{MAESTRO_IP}:{MAESTRO_PORT}/resultado", 
                         json=error_resultado, timeout=HTTP_TIMEOUT)
        except:
            pass
    
    finally:
        # Marcar como no ocupado
        estado_esclavo['ocupado'] = False
        estado_esclavo['trabajo_actual'] = None

@app.route("/estado", methods=["GET"])
def obtener_estado():
    """Obtiene el estado completo del esclavo"""
    info_sistema = obtener_info_sistema()
    
    return jsonify({
        **estado_esclavo,
        **info_sistema,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    print(f"[Esclavo] Iniciando en {ESCLAVO_HOST}:{ESCLAVO_PORT}")
    print(f"[Esclavo] Maestro: {MAESTRO_IP}:{MAESTRO_PORT}")
    print(f"[Esclavo] Algoritmos disponibles: {ALGORITMOS_DISPONIBLES}")
    print(f"[Esclavo] Timeout de algoritmo: {TIMEOUT_ALGORITMO}s")
    
    # Registrarse con el maestro al iniciar
    threading.Timer(5.0, registrar_con_maestro).start()
    
    # Iniciar el servidor Flask
    app.run(host=ESCLAVO_HOST, port=ESCLAVO_PORT, debug=False)
