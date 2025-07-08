from flask import Flask, request, jsonify
import datetime
import threading
import time
import requests
import queue
import psutil
import socket
import os

app = Flask(__name__)

# Configuración desde variables de entorno
MAESTRO_HOST = os.getenv("MAESTRO_HOST", "0.0.0.0")
MAESTRO_PORT = int(os.getenv("MAESTRO_PORT", "5001"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ARCHIVO_TRABAJOS = os.getenv("ARCHIVO_TRABAJOS", "trabajos.txt")
ARCHIVO_RESULTADOS = os.getenv("ARCHIVO_RESULTADOS", "resultados.txt")
PING_TIMEOUT = int(os.getenv("PING_TIMEOUT", "5"))
DISTRIBUCION_INTERVAL = int(os.getenv("DISTRIBUCION_INTERVAL", "2"))
CARGA_AUTO_TRABAJOS = os.getenv("CARGA_AUTO_TRABAJOS", "true").lower() == "true"
MONITOR_ARCHIVO_INTERVAL = int(os.getenv("MONITOR_ARCHIVO_INTERVAL", "30"))
ESCLAVO_PING_INTERVAL = int(os.getenv("ESCLAVO_PING_INTERVAL", "10"))

# Variables globales simples
trabajos_pendientes = queue.Queue()
esclavos = {}
trabajos_completados = []
reportes_memoria = {}
lock = threading.Lock()
trabajos_cargados = False

def cargar_trabajos_desde_archivo(archivo_trabajos=None):
    """Carga trabajos desde un archivo de texto"""
    if archivo_trabajos is None:
        archivo_trabajos = ARCHIVO_TRABAJOS
        
    global trabajos_cargados
    
    if trabajos_cargados:
        print("[Maestro] Los trabajos ya han sido cargados")
        return 0
        
    if not os.path.exists(archivo_trabajos):
        print(f"[Maestro] Archivo de trabajos no encontrado: {archivo_trabajos}")
        return 0
        return 0
        
    trabajos_agregados = 0
    
    try:
        with open(archivo_trabajos, 'r', encoding='utf-8') as f:
            for num_linea, linea in enumerate(f, 1):
                linea = linea.strip()
                
                # Ignorar líneas vacías y comentarios
                if not linea or linea.startswith('#'):
                    continue
                
                try:
                    # Parsear línea: algoritmo,width,height,iteraciones,prioridad
                    partes = linea.split(',')
                    if len(partes) < 4:
                        print(f"[Maestro] Línea {num_linea} inválida: {linea}")
                        continue
                        
                    algoritmo = partes[0].strip()
                    width = int(partes[1].strip())
                    height = int(partes[2].strip())
                    iteraciones = int(partes[3].strip())
                    prioridad = int(partes[4].strip()) if len(partes) > 4 else 1
                    
                    # Crear trabajo
                    trabajo = {
                        'id': f"archivo_trabajo_{trabajos_agregados + 1}",
                        'algoritmo': algoritmo,
                        'width': width,
                        'height': height,
                        'iteraciones': iteraciones,
                        'prioridad': prioridad,
                        'timestamp': time.time(),
                        'origen': 'archivo'
                    }
                    
                    trabajos_pendientes.put(trabajo)
                    trabajos_agregados += 1
                    
                    print(f"[Maestro] Trabajo cargado: {algoritmo} {width}x{height} ({iteraciones} iter, prioridad {prioridad})")
                    
                except (ValueError, IndexError) as e:
                    print(f"[Maestro] Error al parsear línea {num_linea}: {linea} - {e}")
                    continue
                    
        trabajos_cargados = True
        print(f"[Maestro] Se cargaron {trabajos_agregados} trabajos desde {archivo_trabajos}")
        
    except Exception as e:
        print(f"[Maestro] Error al cargar trabajos desde archivo: {e}")
        
    return trabajos_agregados

def monitorear_esclavos():
    """Monitorea constantemente el estado de los esclavos"""
    while True:
        with lock:
            for esclavo_id in list(esclavos.keys()):
                try:
                    # Hacer ping al esclavo
                    response = requests.get(f"http://{esclavos[esclavo_id]['ip']}:{esclavos[esclavo_id]['puerto']}/ping", timeout=PING_TIMEOUT)
                    if response.status_code == 200:
                        data = response.json()
                        esclavos[esclavo_id]['activo'] = True
                        esclavos[esclavo_id]['ultimo_ping'] = time.time()
                        esclavos[esclavo_id]['carga_cpu'] = data.get('cpu_percent', 0)
                        esclavos[esclavo_id]['memoria_libre'] = data.get('memoria_libre', 0)
                        if DEBUG_MODE:
                            print(f"[Maestro] Ping exitoso a {esclavo_id} - CPU: {data.get('cpu_percent', 0)}% - Memoria libre: {data.get('memoria_libre', 0)}MB")
                    else:
                        esclavos[esclavo_id]['activo'] = False
                except Exception as e:
                    esclavos[esclavo_id]['activo'] = False
                    print(f"[Maestro] Error al hacer ping a {esclavo_id}: {e}")
        
        time.sleep(ESCLAVO_PING_INTERVAL)  # Ping configurable

def obtener_esclavo_optimo():
    """Encuentra el esclavo con menor carga y disponible"""
    with lock:
        esclavos_activos = {k: v for k, v in esclavos.items() if v['activo']}
        
        if not esclavos_activos:
            return None
        
        # Buscar esclavo con menor carga de CPU
        mejor_esclavo = None
        menor_carga = float('inf')
        
        for esclavo_id, esclavo_data in esclavos_activos.items():
            carga_cpu = esclavo_data['carga_cpu']
            
            # Considerar también reportes de memoria
            penalizacion = 0
            for nodo, reporte in reportes_memoria.items():
                alertas = reporte.get('alertas', {})
                if any(alertas.values()):
                    penalizacion += 50
            
            carga_total = carga_cpu + penalizacion
            
            if carga_total < menor_carga:
                menor_carga = carga_total
                mejor_esclavo = esclavo_id
        
        if mejor_esclavo:
            print(f"[Maestro] Esclavo óptimo seleccionado: {mejor_esclavo} (carga: {menor_carga})")
        
        return mejor_esclavo

def asignar_trabajo(esclavo_id, trabajo):
    """Asigna un trabajo específico a un esclavo"""
    try:
        esclavo = esclavos[esclavo_id]
        url = f"http://{esclavo['ip']}:{esclavo['puerto']}/ejecutar"
        
        print(f"[Maestro] Asignando trabajo a {esclavo_id}: {trabajo['algoritmo']} {trabajo['width']}x{trabajo['height']}")
        response = requests.post(url, json=trabajo, timeout=30)
        
        if response.status_code == 200:
            print(f"[Maestro] Trabajo asignado exitosamente a {esclavo_id}")
        else:
            print(f"[Maestro] Error al asignar trabajo a {esclavo_id}")
            # Reenviar trabajo a la cola
            trabajos_pendientes.put(trabajo)
            
    except Exception as e:
        print(f"[Maestro] Error al asignar trabajo a {esclavo_id}: {e}")
        trabajos_pendientes.put(trabajo)

def distribuir_trabajos():
    """Distribuye trabajos a esclavos disponibles"""
    while True:
        try:
            if not trabajos_pendientes.empty():
                # Buscar esclavo disponible con menos carga
                esclavo_optimo = obtener_esclavo_optimo()
                
                if esclavo_optimo:
                    trabajo = trabajos_pendientes.get()
                    asignar_trabajo(esclavo_optimo, trabajo)
                else:
                    if DEBUG_MODE:
                        print("[Maestro] No hay esclavos disponibles")
                    
        except Exception as e:
            print(f"[Maestro] Error en distribución de trabajos: {e}")
            
        time.sleep(DISTRIBUCION_INTERVAL)

def cargar_trabajos_automatico():
    """Carga trabajos automáticamente al inicio del sistema"""
    if not CARGA_AUTO_TRABAJOS:
        print("[Maestro] Carga automática de trabajos deshabilitada")
        return
        
    # Esperar un poco para que el sistema se estabilice
    time.sleep(5)
    
    # Cargar trabajos desde archivo
    cargar_trabajos_desde_archivo()
    
    # Monitorear archivo de trabajos periódicamente
    ultimo_tamano = 0
    archivo_trabajos = ARCHIVO_TRABAJOS
    
    while True:
        try:
            if os.path.exists(archivo_trabajos):
                tamano_actual = os.path.getsize(archivo_trabajos)
                if tamano_actual > ultimo_tamano:
                    print("[Maestro] Detectado cambio en archivo de trabajos, recargando...")
                    global trabajos_cargados
                    trabajos_cargados = False
                    cargar_trabajos_desde_archivo()
                    ultimo_tamano = tamano_actual
                    
        except Exception as e:
            print(f"[Maestro] Error monitoreando archivo de trabajos: {e}")
            
        time.sleep(MONITOR_ARCHIVO_INTERVAL)  # Intervalo configurable

# Iniciar hilos al importar
def iniciar_sistema():
    monitor_thread = threading.Thread(target=monitorear_esclavos, daemon=True)
    distribuir_thread = threading.Thread(target=distribuir_trabajos, daemon=True)
    cargar_thread = threading.Thread(target=cargar_trabajos_automatico, daemon=True)
    
    monitor_thread.start()
    distribuir_thread.start()
    cargar_thread.start()
    print("[Maestro] Sistema iniciado")

# Endpoints de la API
@app.route("/ping", methods=["GET"])
def ping():
    """Endpoint para verificar que el maestro está activo"""
    return jsonify({
        "status": "active",
        "timestamp": time.time(),
        "trabajos_pendientes": trabajos_pendientes.qsize(),
        "esclavos_activos": len([e for e in esclavos.values() if e['activo']])
    })

@app.route("/registrar_esclavo", methods=["POST"])
def registrar_esclavo():
    """Registra un nuevo esclavo en el sistema"""
    data = request.get_json()
    esclavo_id = data['esclavo_id']
    ip = data['ip']
    puerto = data.get('puerto', 5002)
    
    with lock:
        esclavos[esclavo_id] = {
            'ip': ip,
            'puerto': puerto,
            'activo': True,
            'ultimo_ping': time.time(),
            'carga_cpu': 0,
            'memoria_libre': 0
        }
    
    print(f"[Maestro] Esclavo {esclavo_id} registrado: {ip}:{puerto}")
    return jsonify({"status": "registered"}), 200

@app.route("/agregar_trabajo", methods=["POST"])
def agregar_trabajo():
    """Agrega un nuevo trabajo a la cola"""
    data = request.get_json()
    trabajo = {
        'id': f"trabajo_{int(time.time())}",
        'algoritmo': data['algoritmo'],
        'width': data['width'],
        'height': data['height'],
        'iteraciones': data['iteraciones'],
        'timestamp': time.time()
    }
    
    trabajos_pendientes.put(trabajo)
    print(f"[Maestro] Trabajo agregado: {trabajo}")
    
    return jsonify({
        "status": "added",
        "trabajo_id": trabajo['id'],
        "posicion_cola": trabajos_pendientes.qsize()
    }), 200

@app.route("/cargar_trabajos", methods=["POST"])
def cargar_trabajos_manual():
    """Carga trabajos manualmente desde archivo"""
    data = request.get_json() or {}
    archivo = data.get('archivo', 'trabajos.txt')
    
    # Reset para permitir recarga
    global trabajos_cargados
    trabajos_cargados = False
    
    trabajos_cargados_count = cargar_trabajos_desde_archivo(archivo)
    
    return jsonify({
        "status": "loaded",
        "trabajos_cargados": trabajos_cargados_count,
        "trabajos_pendientes": trabajos_pendientes.qsize()
    }), 200

@app.route("/limpiar_cola", methods=["POST"])
def limpiar_cola():
    """Limpia la cola de trabajos pendientes"""
    count = 0
    while not trabajos_pendientes.empty():
        trabajos_pendientes.get()
        count += 1
    
    global trabajos_cargados
    trabajos_cargados = False
    
    return jsonify({
        "status": "cleared",
        "trabajos_eliminados": count
    }), 200

@app.route("/estado", methods=["GET"])
def obtener_estado():
    """Obtiene el estado del sistema"""
    with lock:
        estado = {
            "trabajos_pendientes": trabajos_pendientes.qsize(),
            "esclavos": dict(esclavos),
            "trabajos_completados": len(trabajos_completados),
            "trabajos_desde_archivo": trabajos_cargados,
            "timestamp": time.time()
        }
    
    return jsonify(estado)

@app.route("/esclavos", methods=["GET"])
def listar_esclavos():
    """Lista todos los esclavos y su estado"""
    with lock:
        return jsonify(dict(esclavos))

@app.route("/resultado", methods=["POST"])
def recibir_resultado():
    """Recibe resultados de trabajos completados"""
    data = request.get_json()

    linea = f"{datetime.datetime.now()}, {data['esclavo']}, {data['algoritmo']}, {data['resolucion']}, {data['iteraciones']}, {data['tiempo']}s\n"
    
    print("[Maestro] Resultado recibido:", linea.strip())

    with open(ARCHIVO_RESULTADOS, "a") as f:
        f.write(linea)
    
    # Agregar a historial
    with lock:
        trabajos_completados.append({
            **data,
            'timestamp': time.time()
        })

    return jsonify({"status": "received"}), 200

@app.route("/reporte_memoria", methods=["POST"])
def recibir_reporte_memoria():
    """Recibe reportes de memoria de los nodos de monitoreo"""
    data = request.get_json()
    nodo_memoria = data['nodo_memoria']
    
    with lock:
        reportes_memoria[nodo_memoria] = data
    
    print(f"[Maestro] Reporte de memoria recibido de {nodo_memoria}")
    
    # Verificar alertas críticas
    alertas = data.get('alertas', {})
    if any(alertas.values()):
        print(f"[Maestro] ALERTAS ACTIVAS en {nodo_memoria}: {alertas}")
    
    return jsonify({"status": "received"}), 200

@app.route("/memoria", methods=["GET"])
def obtener_estado_memoria():
    """Obtiene el estado de memoria del cluster"""
    with lock:
        return jsonify({
            "reportes": dict(reportes_memoria),
            "timestamp": time.time()
        })

if __name__ == "__main__":
    print(f"[Maestro] Iniciando en {MAESTRO_HOST}:{MAESTRO_PORT}")
    print(f"[Maestro] Archivo de trabajos: {ARCHIVO_TRABAJOS}")
    print(f"[Maestro] Archivo de resultados: {ARCHIVO_RESULTADOS}")
    print(f"[Maestro] Carga automática de trabajos: {CARGA_AUTO_TRABAJOS}")
    print(f"[Maestro] Intervalo de distribución: {DISTRIBUCION_INTERVAL}s")
    
    iniciar_sistema()
    app.run(host=MAESTRO_HOST, port=MAESTRO_PORT, debug=DEBUG_MODE)
