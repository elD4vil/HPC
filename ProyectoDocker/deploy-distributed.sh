#!/bin/bash
# deploy-distributed.sh - Despliega el sistema HPC en VMs distribuidas

echo "🚀 Desplegando sistema HPC distribuido..."

# Variables de configuración
MAESTRO_IP="192.168.56.10"
NODES=("maestro:192.168.56.10" "esclavo1:192.168.56.11" "esclavo2:192.168.56.12" "esclavo3:192.168.56.13")

# Función para ejecutar comandos en una VM
run_on_vm() {
    local vm_name=$1
    local command=$2
    echo "📡 Ejecutando en $vm_name: $command"
    vagrant ssh $vm_name -c "$command"
}

# 1. Desplegar maestro
echo "🧠 Desplegando maestro..."
run_on_vm "maestro" "cd /home/vagrant/hpc && docker-compose up -d maestro memoria1 memoria2"

# Esperar que el maestro esté listo
echo "⏳ Esperando que el maestro esté listo..."
sleep 10

# 2. Desplegar esclavos
for i in {1..3}; do
    echo "💪 Desplegando esclavo$i..."
    run_on_vm "esclavo$i" "cd /home/vagrant/hpc && docker-compose up -d esclavo$i"
    sleep 5
done

echo "✅ Sistema HPC distribuido desplegado exitosamente!"
echo "🌐 Maestro disponible en: http://$MAESTRO_IP:5001"
echo "📊 Para ver estado: vagrant ssh maestro -c 'docker logs hpc-maestro'"
