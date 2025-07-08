# Sistema HPC Distribuido con Docker

Este proyecto implementa un sistema de computación de alto rendimiento (HPC) distribuido usando Docker, con un arquitectura maestro-esclavo y monitoreo de recursos.

## Arquitectura

### Componentes:

1. **Maestro** (Puerto 5001):
   - API REST para gestionar trabajos
   - Cola de trabajos pendientes
   - Distribución inteligente de carga
   - Monitoreo de estado de esclavos
   - Recepción de resultados

2. **Esclavos** (Puertos 5011-5013):
   - API REST para recibir trabajos
   - Ejecución de algoritmos
   - Reporte de estado y recursos
   - Auto-registro con el maestro

3. **Memoria** (Puertos 5003-5004):
   - Monitoreo continuo de recursos del sistema
   - Alertas por alto uso de CPU/memoria/disco
   - Reportes periódicos al maestro

## Flujo de Trabajo

1. **Inicio del Sistema**:
   - Los nodos de memoria inician el monitoreo de recursos
   - Los esclavos se registran automáticamente con el maestro
   - El maestro inicia el monitoreo de esclavos y distribución de trabajos

2. **Distribución de Trabajos**:
   - Cliente envía trabajo al maestro via API
   - Maestro agrega trabajo a la cola
   - Distribuidor selecciona esclavo óptimo basado en:
     - Carga de CPU actual
     - Memoria disponible
     - Alertas de recursos
   - Maestro asigna trabajo al esclavo seleccionado

3. **Ejecución**:
   - Esclavo recibe trabajo y marca como ocupado
   - Ejecuta algoritmo en hilo separado
   - Envía resultado al maestro
   - Se marca como disponible para nuevos trabajos

4. **Monitoreo**:
   - Maestro hace ping a esclavos cada 10 segundos
   - Nodos de memoria reportan métricas cada 30 segundos
   - Sistema detecta y reporta alertas automáticamente

## APIs Disponibles

### Maestro (http://localhost:5001)

- `GET /ping` - Estado del maestro
- `POST /agregar_trabajo` - Agregar trabajo a la cola
- `POST /cargar_trabajos` - Cargar trabajos desde archivo
- `POST /limpiar_cola` - Limpiar cola de trabajos pendientes
- `GET /estado` - Estado completo del sistema
- `GET /esclavos` - Lista de esclavos registrados
- `GET /memoria` - Reportes de memoria del cluster
- `POST /registrar_esclavo` - Registro de nuevos esclavos
- `POST /resultado` - Recepción de resultados
- `POST /reporte_memoria` - Recepción de reportes de memoria

### Esclavos (http://localhost:5011-5013)

- `GET /ping` - Estado del esclavo y métricas de sistema
- `POST /ejecutar` - Ejecutar trabajo asignado
- `GET /estado` - Estado detallado del esclavo

### Memoria (http://localhost:5003-5004)

- `GET /metricas` - Métricas actuales del sistema
- `GET /historial` - Historial de métricas
- `GET /alertas` - Alertas activas
- `GET /ping` - Estado del servicio

## Inicio del Sistema

### 1. Construir y ejecutar con Docker Compose:
```bash
docker-compose up --build
```

### 2. Verificar el estado:
```bash
python cliente_hpc.py --comando estado
```

### 3. Cargar trabajos desde archivo:
```bash
python cliente_hpc.py --comando cargar_trabajos --archivo trabajos.txt
```

### 4. Agregar trabajos individuales:
```bash
python cliente_hpc.py --comando trabajo --algoritmo Secuencial --width 1000 --height 800 --iteraciones 200
```

### 5. Limpiar cola de trabajos:
```bash
python cliente_hpc.py --comando limpiar_cola
```

### 6. Monitoreo continuo:
```bash
python cliente_hpc.py --comando monitorear --intervalo 15
```

### 7. Demostración completa:
```bash
python demo_trabajos.py
```

## Gestión de Trabajos desde Archivo

### Formato del Archivo de Trabajos

El sistema puede cargar trabajos automáticamente desde un archivo de texto (`trabajos.txt`). El formato es:

```
# Comentarios empiezan con #
algoritmo,width,height,iteraciones,prioridad

# Ejemplos:
Secuencial,800,600,100,1
Numpy,1000,800,150,2
juliaCython,1200,900,200,1
```

### Características:

- **Carga Automática**: Los trabajos se cargan automáticamente al iniciar el maestro
- **Monitoreo Continuo**: El archivo se monitorea cada 30 segundos para nuevos trabajos
- **Prioridades**: Los trabajos pueden tener diferentes prioridades (1=alta, 2=media, 3=baja)
- **Comentarios**: Las líneas que empiecen con `#` son ignoradas
- **Recarga Manual**: Se puede forzar la recarga con el comando `cargar_trabajos`

### Comandos Específicos:

```bash
# Cargar trabajos desde archivo específico
python cliente_hpc.py --comando cargar_trabajos --archivo mi_archivo.txt

# Limpiar toda la cola de trabajos
python cliente_hpc.py --comando limpiar_cola

# Ver estado incluyendo información de trabajos desde archivo
python cliente_hpc.py --comando estado
```

## Características Avanzadas

### Distribución Inteligente de Carga:
- Selección de esclavo basada en métricas reales
- Consideración de alertas de memoria
- Balanceo automático de carga

### Tolerancia a Fallos:
- Re-encolado automático de trabajos fallidos
- Detección automática de esclavos inactivos
- Timeouts configurables

### Monitoreo Avanzado:
- Métricas en tiempo real de CPU, memoria y disco
- Historial de rendimiento
- Alertas automáticas por alto uso de recursos

### Escalabilidad:
- Fácil adición de nuevos esclavos
- Configuración flexible via variables de entorno
- Arquitectura distribuida sin puntos únicos de fallo

## Variables de Entorno

- `ESCLAVO`: ID del esclavo (ej: esclavo1, esclavo2)
- `MAESTRO_IP`: IP del maestro (default: maestro)
- `MEMORIA_NODE`: ID del nodo de memoria (ej: memoria1, memoria2)
- `PYTHONUNBUFFERED`: Para logs en tiempo real

## Algoritmos Soportados

El sistema soporta múltiples algoritmos configurados en la carpeta `algoritmos/`:
- Secuencial
- Numpy
- juliaCython (optimizado con Cython)

## Troubleshooting

### Esclavos no se registran:
- Verificar conectividad de red
- Revisar logs del maestro y esclavos
- Confirmar que MAESTRO_IP sea correcta

### Trabajos no se ejecutan:
- Verificar que los esclavos respondan al ping
- Revisar cola de trabajos pendientes
- Confirmar que los algoritmos estén disponibles

### Alertas de memoria:
- Revisar métricas del sistema
- Considerar reducir carga de trabajo
- Evaluar escalamiento horizontal
