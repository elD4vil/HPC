#!/usr/bin/env python3
"""
Script de demostración para la carga de trabajos desde archivo
"""

import time
import os
import sys

# Agregar el directorio actual al path para importar las funciones del cliente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cliente_hpc import ping_maestro, obtener_estado, limpiar_cola_trabajos, cargar_trabajos_desde_archivo, obtener_esclavos, obtener_memoria

def main():
    print("🚀 Demostración del Sistema HPC con carga de trabajos desde archivo")
    print("="*70)
    
    # 1. Verificar estado inicial
    print("\n1️⃣  Verificando estado inicial del sistema...")
    if not ping_maestro():
        print("❌ El maestro no está disponible. Asegúrate de que el sistema esté ejecutándose.")
        return
    
    obtener_estado()
    
    # 2. Limpiar cola si hay trabajos pendientes
    print("\n2️⃣  Limpiando cola de trabajos...")
    limpiar_cola_trabajos()
    
    # 3. Cargar trabajos desde archivo
    print("\n3️⃣  Cargando trabajos desde archivo trabajos.txt...")
    resultado = cargar_trabajos_desde_archivo("trabajos.txt")
    
    if not resultado:
        print("❌ No se pudieron cargar los trabajos")
        return
    
    # 4. Monitorear progreso
    print("\n4️⃣  Monitoreando progreso de trabajos...")
    print("Los trabajos se ejecutarán automáticamente en los esclavos disponibles.")
    print("Presiona Ctrl+C para detener el monitoreo")
    
    try:
        trabajos_iniciales = resultado['trabajos_cargados']
        while True:
            estado = obtener_estado()
            if estado:
                pendientes = estado['trabajos_pendientes']
                completados = estado['trabajos_completados']
                
                print(f"\n📈 Progreso: {completados}/{trabajos_iniciales + completados} trabajos completados")
                print(f"⏳ Pendientes: {pendientes}")
                
                if pendientes == 0:
                    print("\n✅ ¡Todos los trabajos han sido completados!")
                    break
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido por el usuario")
    
    # 5. Estado final
    print("\n5️⃣  Estado final del sistema:")
    obtener_estado()
    obtener_esclavos()
    obtener_memoria()

if __name__ == "__main__":
    main()
