#!/usr/bin/env python3
"""
Cliente simple para el sistema distribuido HPC
"""

import requests
import json
import time
import argparse
import os

# Configuración desde variables de entorno con valores por defecto
MAESTRO_URL = os.getenv("MAESTRO_URL", "http://localhost:5001")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "10"))
ALGORITMO_DEFAULT = os.getenv("ALGORITMO_DEFAULT", "Secuencial")
ARCHIVO_TRABAJOS = os.getenv("ARCHIVO_TRABAJOS", "trabajos.txt")

def ping_maestro():
    """Verifica que el maestro esté activo"""
    try:
        response = requests.get(f"{MAESTRO_URL}/ping", timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Maestro activo - Trabajos pendientes: {data['trabajos_pendientes']}, Esclavos activos: {data['esclavos_activos']}")
            return True
        else:
            print(f"❌ Error al conectar con maestro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
def agregar_trabajo(algoritmo=None, width=800, height=600, iteraciones=100):
    """Agrega un trabajo a la cola"""
    if algoritmo is None:
        algoritmo = ALGORITMO_DEFAULT
        
    trabajo = {
        "algoritmo": algoritmo,
        "width": width,
        "height": height,
        "iteraciones": iteraciones
    }
    
    try:
        response = requests.post(f"{MAESTRO_URL}/agregar_trabajo", json=trabajo, timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Trabajo agregado: {data['trabajo_id']} - Posición en cola: {data['posicion_cola']}")
            return data['trabajo_id']
        else:
            print(f"❌ Error al agregar trabajo: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def cargar_trabajos_desde_archivo(archivo=None):
    """Carga trabajos desde un archivo en el maestro"""
    if archivo is None:
        archivo = ARCHIVO_TRABAJOS
        
    try:
        data = {"archivo": archivo}
        response = requests.post(f"{MAESTRO_URL}/cargar_trabajos", json=data, timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Trabajos cargados desde {archivo}:")
            print(f"   Trabajos cargados: {result['trabajos_cargados']}")
            print(f"   Total pendientes: {result['trabajos_pendientes']}")
            return result
        else:
            print(f"❌ Error al cargar trabajos: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def limpiar_cola_trabajos():
    """Limpia la cola de trabajos pendientes"""
    try:
        response = requests.post(f"{MAESTRO_URL}/limpiar_cola", timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cola de trabajos limpiada:")
            print(f"   Trabajos eliminados: {result['trabajos_eliminados']}")
            return result
        else:
            print(f"❌ Error al limpiar cola: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def obtener_estado():
    """Obtiene el estado del sistema"""
    try:
        response = requests.get(f"{MAESTRO_URL}/estado", timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Estado del Sistema:")
            print(f"   Trabajos pendientes: {data['trabajos_pendientes']}")
            print(f"   Trabajos completados: {data['trabajos_completados']}")
            print(f"   Trabajos desde archivo: {'✅ Sí' if data.get('trabajos_desde_archivo', False) else '❌ No'}")
            print(f"   Esclavos registrados: {len(data['esclavos'])}")
            
            print("\n🖥️  Estado de Esclavos:")
            for esclavo_id, info in data['esclavos'].items():
                estado = "🟢 Activo" if info['activo'] else "🔴 Inactivo"
                print(f"   {esclavo_id}: {estado} - CPU: {info.get('carga_cpu', 0):.1f}% - Memoria libre: {info.get('memoria_libre', 0):.0f}MB")
            
            return data
        else:
            print(f"❌ Error al obtener estado: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def obtener_esclavos():
    """Lista todos los esclavos y su estado"""
    try:
        response = requests.get(f"{MAESTRO_URL}/esclavos", timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            esclavos = response.json()
            print("\n👥 Esclavos Registrados:")
            for esclavo_id, info in esclavos.items():
                estado = "🟢" if info['activo'] else "🔴"
                ultimo_ping = time.time() - info.get('ultimo_ping', 0)
                print(f"   {estado} {esclavo_id} ({info['ip']}:{info['puerto']}) - Último ping: {ultimo_ping:.1f}s")
            return esclavos
        else:
            print(f"❌ Error al obtener esclavos: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def obtener_memoria():
    """Obtiene reportes de memoria"""
    try:
        response = requests.get(f"{MAESTRO_URL}/memoria", timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print("\n💾 Estado de Memoria:")
            for nodo, reporte in data['reportes'].items():
                alertas = reporte.get('alertas', {})
                alertas_activas = [k for k, v in alertas.items() if v]
                
                metricas = reporte.get('metricas_actuales', {})
                cpu = metricas.get('cpu', {}).get('percent', 0)
                memoria = metricas.get('memoria', {}).get('percent', 0)
                
                estado_alertas = f"⚠️  {alertas_activas}" if alertas_activas else "✅ Normal"
                print(f"   {nodo}: CPU {cpu:.1f}% - Memoria {memoria:.1f}% - {estado_alertas}")
            
            return data
        else:
            print(f"❌ Error al obtener estado de memoria: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    
def monitorear_sistema(intervalo=10):
    """Monitorea el sistema continuamente"""
    print(f"🔄 Iniciando monitoreo del sistema (cada {intervalo}s)...")
    print("Presiona Ctrl+C para detener")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if ping_maestro():
                obtener_estado()
                obtener_esclavos()
                obtener_memoria()
            
            time.sleep(intervalo)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido")

def main():
    parser = argparse.ArgumentParser(description="Cliente para el sistema HPC distribuido")
    parser.add_argument("--maestro", default=MAESTRO_URL, help=f"URL del maestro (default: {MAESTRO_URL})")
    parser.add_argument("--comando", choices=["ping", "estado", "esclavos", "memoria", "trabajo", "monitorear", "cargar_trabajos", "limpiar_cola"], 
                       default="estado", help="Comando a ejecutar")
    parser.add_argument("--algoritmo", default=ALGORITMO_DEFAULT, help=f"Algoritmo para el trabajo (default: {ALGORITMO_DEFAULT})")
    parser.add_argument("--width", type=int, default=800, help="Ancho para el trabajo")
    parser.add_argument("--height", type=int, default=600, help="Alto para el trabajo")
    parser.add_argument("--iteraciones", type=int, default=100, help="Iteraciones para el trabajo")
    parser.add_argument("--intervalo", type=int, default=10, help="Intervalo de monitoreo en segundos")
    parser.add_argument("--archivo", default=ARCHIVO_TRABAJOS, help=f"Archivo de trabajos a cargar (default: {ARCHIVO_TRABAJOS})")
    
    args = parser.parse_args()
    
    # Actualizar URL del maestro si se especifica
    global MAESTRO_URL
    MAESTRO_URL = args.maestro
    
    print(f"🔗 Conectando a maestro: {MAESTRO_URL}")
    print(f"⏱️  Timeout HTTP: {HTTP_TIMEOUT}s")
    
    if args.comando == "ping":
        ping_maestro()
    elif args.comando == "estado":
        obtener_estado()
    elif args.comando == "esclavos":
        obtener_esclavos()
    elif args.comando == "memoria":
        obtener_memoria()
    elif args.comando == "trabajo":
        agregar_trabajo(args.algoritmo, args.width, args.height, args.iteraciones)
    elif args.comando == "cargar_trabajos":
        cargar_trabajos_desde_archivo(args.archivo)
    elif args.comando == "limpiar_cola":
        limpiar_cola_trabajos()
    elif args.comando == "monitorear":
        monitorear_sistema(args.intervalo)

if __name__ == "__main__":
    main()
