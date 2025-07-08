from flask import Flask, jsonify
import psutil
import time
import threading
import requests
import os

app = Flask(__name__)

# Historial de métricas del sistema
metricas_historial = []
MAX_HISTORIAL = 100

class MonitorMemoria:
    def __init__(self):
        self.monitor_thread = threading.Thread(target=self.monitorear_sistema, daemon=True)
        self.reporte_thread = threading.Thread(target=self.reportar_a_maestro, daemon=True)
        
    def iniciar(self):
        self.monitor_thread.start()
        self.reporte_thread.start()
        print("[Memoria] Monitor iniciado")
        
    def obtener_metricas(self):
        """Obtiene métricas actuales del sistema"""
        cpu = psutil.cpu_percent(interval=1)
        memoria = psutil.virtual_memory()
        disco = psutil.disk_usage('/')
        red = psutil.net_io_counters()
        
        metricas = {
            'timestamp': time.time(),
            'cpu': {
                'percent': cpu,
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memoria': {
                'total': memoria.total,
                'disponible': memoria.available,
                'usado': memoria.used,
                'libre': memoria.free,
                'percent': memoria.percent
            },
            'disco': {
                'total': disco.total,
                'usado': disco.used,
                'libre': disco.free,
                'percent': disco.percent
            },
            'red': {
                'bytes_enviados': red.bytes_sent,
                'bytes_recibidos': red.bytes_recv,
                'paquetes_enviados': red.packets_sent,
                'paquetes_recibidos': red.packets_recv
            }
        }
        
        return metricas
        
    def monitorear_sistema(self):
        """Monitorea continuamente las métricas del sistema"""
        while True:
            try:
                metricas = self.obtener_metricas()
                metricas_historial.append(metricas)
                
                # Mantener solo las últimas N métricas
                if len(metricas_historial) > MAX_HISTORIAL:
                    metricas_historial.pop(0)
                    
                # Alertas por alto uso de recursos
                if metricas['cpu']['percent'] > 80:
                    print(f"[Memoria] ALERTA: Alto uso de CPU: {metricas['cpu']['percent']}%")
                    
                if metricas['memoria']['percent'] > 85:
                    print(f"[Memoria] ALERTA: Alta utilización de memoria: {metricas['memoria']['percent']}%")
                    
                if metricas['disco']['percent'] > 90:
                    print(f"[Memoria] ALERTA: Alto uso de disco: {metricas['disco']['percent']}%")
                    
            except Exception as e:
                print(f"[Memoria] Error al obtener métricas: {e}")
                
            time.sleep(5)  # Monitorear cada 5 segundos
            
    def reportar_a_maestro(self):
        """Reporta métricas al maestro periódicamente"""
        while True:
            try:
                if metricas_historial:
                    ultima_metrica = metricas_historial[-1]
                    
                    # Calcular promedios de los últimos 10 registros
                    ultimas_10 = metricas_historial[-10:] if len(metricas_historial) >= 10 else metricas_historial
                    
                    cpu_promedio = sum(m['cpu']['percent'] for m in ultimas_10) / len(ultimas_10)
                    memoria_promedio = sum(m['memoria']['percent'] for m in ultimas_10) / len(ultimas_10)
                    
                    reporte = {
                        'nodo_memoria': os.getenv("MEMORIA_NODE", "memoria1"),
                        'timestamp': time.time(),
                        'metricas_actuales': ultima_metrica,
                        'promedios': {
                            'cpu_percent': cpu_promedio,
                            'memoria_percent': memoria_promedio
                        },
                        'alertas': {
                            'cpu_alto': cpu_promedio > 80,
                            'memoria_alta': memoria_promedio > 85,
                            'disco_alto': ultima_metrica['disco']['percent'] > 90
                        }
                    }
                    
                    # Enviar al maestro
                    maestro_ip = os.getenv("MAESTRO_IP", "maestro")
                    requests.post(f"http://{maestro_ip}:5001/reporte_memoria", 
                                json=reporte, timeout=10)
                                
            except Exception as e:
                print(f"[Memoria] Error al reportar al maestro: {e}")
                
            time.sleep(30)  # Reportar cada 30 segundos

# Instancia global del monitor
monitor = MonitorMemoria()

@app.route("/metricas", methods=["GET"])
def obtener_metricas():
    """Obtiene las métricas actuales del sistema"""
    try:
        metricas = monitor.obtener_metricas()
        return jsonify(metricas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/historial", methods=["GET"])
def obtener_historial():
    """Obtiene el historial de métricas"""
    return jsonify({
        "historial": metricas_historial,
        "total_registros": len(metricas_historial)
    })

@app.route("/alertas", methods=["GET"])
def obtener_alertas():
    """Obtiene alertas activas basadas en las métricas actuales"""
    if not metricas_historial:
        return jsonify({"alertas": []})
        
    ultima_metrica = metricas_historial[-1]
    alertas = []
    
    if ultima_metrica['cpu']['percent'] > 80:
        alertas.append({
            "tipo": "cpu_alta",
            "mensaje": f"Alto uso de CPU: {ultima_metrica['cpu']['percent']}%",
            "valor": ultima_metrica['cpu']['percent'],
            "timestamp": ultima_metrica['timestamp']
        })
    
    if ultima_metrica['memoria']['percent'] > 85:
        alertas.append({
            "tipo": "memoria_alta", 
            "mensaje": f"Alta utilización de memoria: {ultima_metrica['memoria']['percent']}%",
            "valor": ultima_metrica['memoria']['percent'],
            "timestamp": ultima_metrica['timestamp']
        })
        
    if ultima_metrica['disco']['percent'] > 90:
        alertas.append({
            "tipo": "disco_alto",
            "mensaje": f"Alto uso de disco: {ultima_metrica['disco']['percent']}%", 
            "valor": ultima_metrica['disco']['percent'],
            "timestamp": ultima_metrica['timestamp']
        })
    
    return jsonify({"alertas": alertas})

@app.route("/ping", methods=["GET"])
def ping():
    """Ping para verificar que el servicio está activo"""
    return jsonify({
        "status": "active",
        "timestamp": time.time(),
        "total_metricas": len(metricas_historial)
    })

if __name__ == "__main__":
    monitor.iniciar()
    app.run(host="0.0.0.0", port=5003, debug=False)