# Sistema HPC Distribuido con Docker Registry

Este proyecto implementa un sistema de computación de alto rendimiento (HPC) distribuido usando **Docker Registry** y **Vagrant**, con una arquitectura maestro-esclavo distribuida en múltiples máquinas virtuales para máximo realismo.

## 🏗️ Arquitectura Distribuida

### Topología de Red:
```
Registry Local (192.168.56.1:5000)
       ↓
VM Maestro (192.168.56.10)
├── Container: maestro (Puerto 5001)
├── Container: memoria1 (Puerto 5003)  
└── Container: memoria2 (Puerto 5004)
       ↓ (Red privada)
VM Esclavo1 (192.168.56.11)        VM Esclavo2 (192.168.56.12)
└── Container: esclavo1 (5002)      └── Container: esclavo2 (5002)
```

### Componentes del Sistema:

#### 🧠 **Nodo Maestro** (VM: 192.168.56.10)
- **Maestro** (Puerto 5001):
  - API REST para gestión centralizada de trabajos
  - Cola distribuida de trabajos pendientes
  - **Distribución inteligente** basada en métricas en tiempo real
  - Monitoreo continuo de salud de esclavos
  - Agregación de resultados del cluster

- **Memoria1 & Memoria2** (Puertos 5003-5004):
  - **Monitoreo distribuido** de recursos del cluster
  - Alertas automáticas por saturación de recursos
  - Métricas centralizadas de CPU/memoria/disco
  - Reportes periódicos al maestro

#### 💪 **Nodos Esclavos** (VMs: 192.168.56.11-12)
- **Esclavos** (Puerto 5002 cada uno):
  - API REST para recepción de trabajos
  - **Ejecución paralela** de algoritmos computacionales
  - Auto-registro dinámico con el maestro
  - Reporte en tiempo real de estado y recursos

#### 🐳 **Docker Registry** (192.168.56.1:5000)
- **Distribución centralizada** de imágenes Docker
- Versionado consistente entre todas las VMs
- Despliegue sincronizado del software HPC

## 🔄 Flujo de Trabajo Distribuido

### 1. **Inicialización del Cluster**:
   ```
   Registry → Distribución de imágenes → VMs
   ├── VM Maestro: Inicia servicios centrales
   ├── VM Esclavo1: Auto-registro con maestro
   └── VM Esclavo2: Auto-registro con maestro
   ```

### 2. **Distribución Inteligente de Trabajos**:
   ```
   Cliente → Maestro → Análisis de carga → Selección de esclavo óptimo
   ```
   - **Métricas consideradas**:
     - Carga de CPU por esclavo
     - Memoria disponible en tiempo real
     - Latencia de red entre nodos
     - Alertas de saturación de recursos
   - **Algoritmos de selección**:
     - Round-robin con balance de carga
     - Priorización por recursos disponibles

### 3. **Ejecución Distribuida**:
   ```
   Maestro → Esclavo seleccionado → Ejecución → Resultado → Maestro
   ```
   - Ejecución en **hilos separados** para paralelismo
   - **Tolerancia a fallos** con re-encolado automático
   - Timeout configurable por trabajo

### 4. **Monitoreo del Cluster**:
   ```
   Nodos Memoria → Métricas → Maestro → Dashboard centralizado
   ```
   - Ping distribuido cada 10 segundos
   - Reportes de memoria cada 30 segundos
   - **Alertas automáticas** por saturación

## 🌐 APIs del Sistema Distribuido

### 🧠 Maestro Centralizado (http://192.168.56.10:5001)

#### **Gestión de Trabajos**:
- `POST /agregar_trabajo` - Agregar trabajo individual al cluster
- `POST /cargar_trabajos` - Carga masiva desde archivo
- `POST /limpiar_cola` - Limpieza de cola distribuida
- `GET /estado` - **Estado completo del cluster**

#### **Gestión de Cluster**:
- `GET /esclavos` - Lista de nodos esclavos activos
- `GET /memoria` - **Métricas agregadas del cluster**
- `POST /registrar_esclavo` - Auto-registro de nuevos nodos
- `POST /resultado` - Recepción de resultados distribuidos

### 💪 Esclavos Distribuidos (192.168.56.11:5002, 192.168.56.12:5002)

- `GET /ping` - **Métricas de nodo** (CPU, memoria, carga)
- `POST /ejecutar` - Ejecución de trabajo asignado
- `GET /estado` - Estado detallado del nodo esclavo

### 📊 Nodos de Memoria (192.168.56.10:5003-5004)

- `GET /metricas` - **Métricas en tiempo real**
- `GET /historial` - Historial de rendimiento
- `GET /alertas` - **Alertas activas del cluster**

## 🚀 Despliegue del Sistema Distribuido

### **Opción 1: Despliegue Automatizado Completo**

```bash
# 1. Construir y publicar imágenes en registry
./build-all-images.sh

# 2. Crear cluster completo (4 VMs + Registry)
./full-deploy.sh

# 3. Monitorear despliegue
vagrant status
```

### **Opción 2: Despliegue Manual Paso a Paso**

```bash
# 1. Crear Docker Registry local
docker run -d -p 5000:5000 --name registry registry:2

# 2. Construir y publicar imágenes
docker build -t localhost:5000/hpc-maestro:latest ./maestro
docker build -t localhost:5000/hpc-memoria:latest ./memoria
docker build -t localhost:5000/hpc-esclavo:latest ./esclavo

docker push localhost:5000/hpc-maestro:latest
docker push localhost:5000/hpc-memoria:latest
docker push localhost:5000/hpc-esclavo:latest

# 3. Crear cluster de VMs
vagrant up

# 4. Desplegar servicios distribuidos
./deploy-distributed.sh
```

### **Opción 3: Despliegue con PowerShell (Windows)**

```powershell
# Despliegue completo desde PowerShell
.\deploy-distributed.ps1
```

## 📋 Gestión de Trabajos Distribuidos

### **Comandos del Cliente HPC**:

```bash
# Estado completo del cluster distribuido
python cliente_hpc.py --comando estado

# Carga masiva de trabajos al cluster  
python cliente_hpc.py --comando cargar_trabajos --archivo trabajos.txt

# Trabajo individual con distribución automática
python cliente_hpc.py --comando trabajo --algoritmo juliaCython --width 2000 --height 1500 --iteraciones 500

# Monitoreo continuo del cluster
python cliente_hpc.py --comando monitorear --intervalo 10

# Demostración del sistema distribuido
python demo_trabajos.py
```

### **Formato de Archivo de Trabajos** (`maestro/trabajos.txt`):

```
# Trabajos de alta prioridad
Secuencial,3000,2400,1000,1
Numpy,3200,2500,1200,2
juliaCython,3500,2800,1500,1

# Trabajos de estrés para cluster
Secuencial,4000,3000,2000,3
Numpy,4500,3500,2500,2
juliaCython,5000,4000,3000,1
```

## 🔧 Características Avanzadas del Sistema Distribuido

### **Distribución Inteligente**:
- **Balanceador de carga** basado en métricas reales
- **Selección dinámica** del nodo óptimo
- **Prevención de saturación** mediante alertas

### **Alta Disponibilidad**:
- **Tolerancia a fallos** de nodos individuales
- **Re-encolado automático** de trabajos fallidos
- **Recuperación automática** de nodos

### **Escalabilidad Horizontal**:
- **Adición dinámica** de nuevos nodos esclavos
- **Auto-descubrimiento** de servicios
- **Particionamiento automático** de carga

### **Monitoreo Distribuido**:
- **Métricas agregadas** de todo el cluster
- **Dashboards centralizados** de rendimiento
- **Alertas proactivas** por degradación

## 🌐 Arquitectura de Red

### **Configuración de Red Privada**:
```
192.168.56.0/24 (Red privada Vagrant)
├── 192.168.56.1:5000   → Docker Registry
├── 192.168.56.10:5001  → VM Maestro (+ memoria1,2)
├── 192.168.56.11:5002  → VM Esclavo1
└── 192.168.56.12:5002  → VM Esclavo2
```

### **Acceso desde Host**:
- **Maestro**: http://192.168.56.10:5001
- **Registry**: http://localhost:5000
- **SSH a nodos**: `vagrant ssh maestro|esclavo1|esclavo2`

## 📊 Monitoreo y Métricas

### **Comandos de Monitoreo**:

```bash
# Ver estado de todo el cluster
vagrant status

# Logs del maestro en tiempo real
vagrant ssh maestro -c "docker-compose logs -f maestro"

# Métricas de un esclavo específico
vagrant ssh esclavo1 -c "curl http://localhost:5002/ping"

# Conectividad entre nodos
vagrant ssh esclavo1 -c "ping -c 3 192.168.56.10"

# Trabajos completados
vagrant ssh maestro -c "cat /vagrant/maestro/resultados.txt | tail -10"
```

### **Métricas del Sistema**:
- **CPU**: Utilización por nodo y agregada
- **Memoria**: Uso actual y disponible
- **Red**: Latencia entre nodos
- **Trabajos**: Cola, completados, fallidos
- **Alertas**: Saturación, timeouts, errores

## 🛠️ Gestión del Cluster

### **Comandos de Gestión**:

```bash
# Reiniciar cluster completo
vagrant reload

# Reiniciar nodo específico
vagrant reload esclavo1

# Actualizar imágenes en cluster
docker push localhost:5000/hpc-maestro:latest
vagrant ssh maestro -c "docker-compose pull && docker-compose up -d"

# Escalar cluster (agregar esclavo)
# Modificar Vagrantfile y ejecutar:
vagrant up esclavo3
```

### **Troubleshooting Distribuido**:

```bash
# Verificar registry
curl http://localhost:5000/v2/_catalog

# Verificar conectividad cluster
vagrant ssh maestro -c "ping -c 2 192.168.56.11"
vagrant ssh maestro -c "ping -c 2 192.168.56.12"

# Ver logs de despliegue
vagrant ssh maestro -c "docker-compose logs"

# Reiniciar servicios específicos
vagrant ssh maestro -c "docker-compose restart maestro"
```

## 📈 Optimizaciones de Rendimiento

### **Configuración de VMs**:
- **Maestro**: 2 CPU, 2GB RAM (servicios centrales)
- **Esclavos**: 1 CPU, 1GB RAM (ejecución optimizada)

### **Optimizaciones de Red**:
- Red privada dedicada para comunicación cluster
- Registry local para distribución rápida de imágenes

### **Algoritmos Optimizados**:
- **Secuencial**: Implementación básica Python
- **Numpy**: Optimización vectorizada
- **juliaCython**: Compilación JIT para máximo rendimiento

## 🎯 Casos de Uso

### **Desarrollo y Testing**:
- Simulación de entornos de producción distribuidos
- Testing de tolerancia a fallos
- Validación de algoritmos paralelos

### **Educación**:
- Demostración de conceptos HPC
- Práctica con sistemas distribuidos
- Monitoreo de recursos en tiempo real

### **Prototipado**:
- Validación de arquitecturas distribuidas
- Benchmarking de algoritmos
- Pruebas de escalabilidad

---

**Sistema HPC Distribuido - Computación de Alto Rendimiento con Docker Registry y