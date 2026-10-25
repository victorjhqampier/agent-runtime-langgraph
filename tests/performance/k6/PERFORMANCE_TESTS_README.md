# K6 Performance Tests - Complete Guide

Guía completa de tests de performance para los 3 controladores principales usando k6.

## 📋 Contenido

1. [Estructura](#estructura)
2. [Controladores testeados](#controladores-testeados)
3. [Instalación](#instalación)
4. [Ejecución rápida](#ejecución-rápida)
5. [Tests por tipo](#tests-por-tipo)
6. [Parámetros y configuración](#parámetros-y-configuración)
7. [Interpretación de resultados](#interpretación-de-resultados)

---

## 📁 Estructura

```
tests/performance/k6/
├── config/
│   ├── environments.js        # Configuración de ambientes (parametrizable)
│   └── thresholds.js          # Umbrales de éxito por tipo de test
├── data/
│   └── example-requests.json  # Datos de prueba (sin secretos)
├── shared/
│   ├── http-client.js         # HTTP client reutilizable
│   ├── request-builder.js     # Constructores de requests por endpoint
│   └── metrics.js             # Registro de métricas
├── rps/                       # Tests de Requests Per Second
│   ├── bian-example.rps.js
│   ├── no-bian-example.rps.js
│   └── no-bian-redis.rps.js
├── smoke/                     # Tests de validación rápida
│   ├── basic-health-check.smoke.js
│   └── endpoints-validation.smoke.js
├── stress/                    # Tests de límites
│   └── concurrent-load.stress.js
├── soak/                      # Tests de resistencia a largo plazo
│   └── long-running.soak.js
├── run-tests.sh               # Script para ejecutar todos los tests
└── README.md                  # Este archivo
```

## 🎯 Controladores testeados

### 1. BianExampleController
- **Endpoint 1:** `POST /{customer_id}/create` (sin auth)
- **Endpoint 2:** `POST /new/create` (con auth Cognito)
- **Usecase:** ExampleUsecase
- **Timeout:** 9 segundos

### 2. NoBianExampleController
- **Endpoint:** `POST /{customer_id}/create`
- **Usecase:** ExampleUsecase (sin caché)
- **Timeout:** 9 segundos

### 3. NoBianExampleRedisController
- **Endpoint:** `POST /{customer_id}/create-redis`
- **Usecase:** ExampleRedisUsecase (con caché Redis)
- **TTL Caché:** 5 minutos
- **Timeout:** 9 segundos

---

## 💻 Instalación

### Requisitos
- Node.js 14+ (o k6 directo sin Node)
- k6 instalado: https://k6.io/docs/getting-started/installation/

### Instalación de k6 en macOS
```bash
brew install k6
```

### Verificar instalación
```bash
k6 version
```

---

## 🚀 Ejecución rápida

### 1. Asegúrate que el servidor está corriendo
```bash
# Desde src/
uvicorn Presentation.app:app --reload
# Output: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2. Ejecuta tests desde tests/performance/k6/

```bash
# SMOKE: Validación rápida (10-20 segundos)
k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000

# RPS: Requests per second (30-50 segundos)
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s

# STRESS: Encontrar límites (60 segundos)
k6 run stress/concurrent-load.stress.js --env BASE_URL=http://127.0.0.1:8000

# SOAK: Resistencia (300 segundos / 5 minutos)
k6 run soak/long-running.soak.js --env BASE_URL=http://127.0.0.1:8000 --vus 30
```

---

## 📊 Tests por tipo

### SMOKE Tests (🔥 Rápido: 10-20s)

**Propósito:** Validación rápida de disponibilidad

#### Health Check
```bash
k6 run smoke/basic-health-check.smoke.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 1 \
  --duration 10s
```

**Valida:**
- Endpoint `/health` disponible
- Todos los 3 controladores responden

#### Endpoints Validation
```bash
k6 run smoke/endpoints-validation.smoke.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 5 \
  --duration 20s
```

**Valida:**
- Latencia < 2s en todos los endpoints
- Status 200 en respuestas normales
- Manejo correcto de errores

---

### RPS Tests (📈 Rendimiento: 30-50s)

**Propósito:** Medir solicitudes por segundo que soporta cada endpoint

#### BianExampleController
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 50 \
  --duration 30s
```

**Objetivo:** 100+ RPS  
**Stages:**
- 0-5s: Ramp-up a 10 VUs
- 5-20s: Ramp-up a 50 VUs
- 20-30s: Ramp-down a 0 VUs

#### NoBianExampleController
```bash
k6 run rps/no-bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 50 \
  --duration 30s
```

**Objetivo:** 100+ RPS

#### NoBianExampleRedisController (con caché)
```bash
k6 run rps/no-bian-redis.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 75 \
  --duration 30s
```

**Objetivo:** 150+ RPS (mejor rendimiento gracias a caché)

---

### STRESS Test (💥 Límites: 60s)

**Propósito:** Encontrar punto de ruptura del sistema

```bash
k6 run stress/concurrent-load.stress.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 200 \
  --duration 60s
```

**Stages:**
- 0-10s: Ramp-up a 50 VUs (33 RPS)
- 10-20s: Ramp-up a 100 VUs (67 RPS)
- 20-30s: Ramp-up a 150 VUs (100 RPS)
- 30-45s: Ramp-up a 200 VUs (133+ RPS)
- 45-55s: Mantener 200 VUs
- 55-60s: Ramp-down a 0

**Observar:**
- ¿En qué punto aumentan los errores?
- ¿Dónde se dispara la latencia?
- ¿Hay timeouts (408)?

---

### SOAK Test (🧊 Resistencia: 300s)

**Propósito:** Validar estabilidad a largo plazo (memory leaks, connection pools)

```bash
k6 run soak/long-running.soak.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --vus 30 \
  --duration 300s
```

**Duration:** 5 minutos con 30 VUs constantes  

**Stages:**
- 0-30s: Ramp-up a 15 VUs
- 30-60s: Ramp-up a 30 VUs
- 60-240s: **Mantener 30 VUs por 3 minutos**
- 240-300s: Ramp-down a 0

**Observar:**
- ¿Se incrementan errores con el tiempo?
- ¿La latencia se degrada?
- ¿Hay cambios en garbage collection?

---

## 🔧 Parámetros y configuración

### Variables de línea de comandos

```bash
# URL Base (REQUERIDO si no es localhost:8000)
--env BASE_URL=http://127.0.0.1:8000

# Virtual Users
--vus 50

# Duración
--duration 30s

# Device Identifier (Header)
--env DEVICE_ID=mobile-test-device

# Customer ID (Path parameter)
--env CUSTOMER_ID=12345

# Channel (Header)
--env CHANNEL_ID=WEB
```

### Ejemplo: Test con parámetros personalizados
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env DEVICE_ID=custom-device \
  --env CUSTOMER_ID=99999 \
  --vus 100 \
  --duration 60s
```

---

## 📈 Interpretación de resultados

### Métricas clave

**http_reqs**
- Total de requests ejecutados
- Goal: > objetivo de RPS

**http_req_failed**
- Tasa de fallos (respuestas non-2xx)
- Goal: < 1% (0.01)

**http_req_duration**
- Latencia de requests
- p95: 95% de requests por debajo
- p99: 99% de requests por debajo
- Goal: p95 < 500-700ms, p99 < 1000-1500ms

**checks**
- Validaciones lógicas (status, headers, etc)
- Goal: > 99% (0.99)

### Ejemplo de salida exitosa

```
✓ [✓] http_reqs: 3000 (target 100 achieved)
✓ [✓] http_req_failed: 0.00% (< 1%)
✓ [✓] http_req_duration: p(95)=450ms (< 500ms)
✓ [✓] http_req_duration: p(99)=800ms (< 1000ms)
✓ [✓] checks: 99.8% (> 99%)

✓ Test passed
```

### Ejemplo de salida con fallos

```
✗ [✗] http_reqs: 45 (target 100 failed)
✗ [✗] http_req_failed: 5.2% (< 1% failed)
✓ [✓] http_req_duration: p(95)=2300ms
✗ [✗] http_req_duration: p(99)=3500ms (< 1000ms failed)
✓ [✓] checks: 94.8% (> 99% failed)

✗ 3 thresholds failed
```

**Interpretación:**
- No alcanza objetivo de RPS
- Hay errores (5.2%)
- Latencia muy alta (p95=2.3s, p99=3.5s)
- → Aumentar recursos o investigar cuello de botella

---

## 🔍 Debugging

### Ver logs detallados
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  -v  # Verbose
```

### Generar reporte JSON
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --out json=results.json

# Luego analizar resultados.json
```

### Ejecutar test específico vs todos
```bash
# Solo smoke
k6 run smoke/basic-health-check.smoke.js

# Solo RPS de un controller
k6 run rps/no-bian-redis.rps.js

# Todos (usar script run-tests.sh)
bash run-tests.sh all
```

---

## 📝 Headers requeridos

Todos los endpoints requieren estos headers:

```
device_identifier: string    # ID del dispositivo
message_identifier: string   # ID único del mensaje
channel_identifier: string   # Canal (WEB, MOBILE, API, INTERNAL)
```

Se envían automáticamente desde `shared/request-builder.js`

---

## 🎯 Flujo recomendado

1. **Smoke (5 min):** Valida que todo funciona
2. **RPS (10-15 min):** Mide capacidad de cada endpoint
3. **Stress (5 min):** Identifica límites
4. **Soak (10 min):** Valida estabilidad a largo plazo

**Tiempo total:** ~30-40 minutos

---

## ❌ TPS Tests (NO Incluido)

Per requisito: "No tocaremos TPS/"

Los tests TPS están en `tps/` pero NO se incluyen en esta suite para evaluación de los 3 controladores.

---

## 📞 Soporte

- Documentación k6: https://k6.io/docs/
- Código fuente: `tests/performance/k6/`
- Configuración local: `config/environments.js`
- Requests personalizadas: `shared/request-builder.js`

---

**Actualizado:** 30/05/2026
