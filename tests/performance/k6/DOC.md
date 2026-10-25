# Guía de k6 - Pruebas de Performance

Documentación completa para ejecutar y entender pruebas de carga, estrés y resistencia con k6 en este proyecto.

---

## Índice

1. [Conceptos base](#conceptos-base)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Instalación y configuración](#instalación-y-configuración)
4. [Ejecución de pruebas](#ejecución-de-pruebas)
5. [RPS - Requests Per Second](#rps---requests-per-second)
6. [TPS - Transactions Per Second](#tps---transactions-per-second)
7. [Smoke - Validación rápida](#smoke---validación-rápida)
8. [Stress - Encontrar límites](#stress---encontrar-límites)
9. [Soak - Resistencia a largo plazo](#soak---resistencia-a-largo-plazo)
10. [Shared - Código reutilizable](#shared---código-reutilizable)
11. [Config - Configuración centralizada](#config---configuración-centralizada)
12. [Data - Datos de prueba](#data---datos-de-prueba)
13. [Troubleshooting](#troubleshooting)

---

## Conceptos base

### k6

**k6** es un tool de pruebas de rendimiento escrito en Go. Permite escribir escenarios en JavaScript para simular tráfico contra APIs.

Responde preguntas como:
- ¿Cuántas requests por segundo soporta mi API?
- ¿Cuál es el p95 de latencia bajo carga?
- ¿El sistema degradar después de varias horas?
- ¿A partir de qué carga empieza a fallar?

### RPS (Requests Per Second)

**RPS** mide peticiones HTTP por segundo en un endpoint específico.

Ejemplo:
```text
GET /products soporta 500 RPS con p95 < 300 ms
```

Diseño en k6:
```text
1 iteración = 1 request HTTP
rate: 100 = 100 RPS
```

### TPS (Transactions Per Second)

**TPS** mide transacciones completas de negocio por segundo.

Una transacción puede contener múltiples requests.

Ejemplo:
```text
1 checkout = 1 TPS (aunque tenga 5 requests internas)
20 TPS x 5 requests = ~100 RPS
```

### VU (Virtual User)

Un usuario virtual simulado. k6 ejecuta el script en paralelo usando VUs para generar tráfico.

En `constant-arrival-rate`, los VUs se escalan automáticamente para cumplir la tasa objetivo.

### Iteración

Una ejecución completa de la función principal del script.

```javascript
export default function () {
  // Una iteración = aquí
}
```

Puede representar 1 request o 1 transacción completa según el diseño.

### Checks

Validaciones dentro del script que NO detienen la prueba si fallan.

```javascript
check(response, {
  'status es 200': (r) => r.status === 200,
});
```

### Thresholds

Límites de aceptación que SÍ hacen fallar la prueba si se violan.

```javascript
thresholds: {
  http_req_failed: ['rate<0.01'],      // < 1% de errores
  http_req_duration: ['p(95)<500'],    // p95 < 500 ms
}
```

### p95 y p99

Percentiles de latencia.

```text
p95 < 500 ms  = 95% de respuestas tardaron menos de 500 ms
p99 < 1000 ms = 99% de respuestas tardaron menos de 1000 ms
```

---

## Estructura del proyecto

```text
tests/
  performance/
    k6/
      DOC.md                          # Esta guía

      config/
        environments.js               # URLs por ambiente
        thresholds.js                 # Thresholds comunes
      
      shared/
        auth.js                       # Autenticación
        http-client.js                # Cliente HTTP
        metrics.js                    # Métricas custom
      
      data/
        users.csv                     # Usuarios de prueba
        products.json                 # Productos de prueba
      
      rps/
        get-users.rps.js              # RPS: GET /users
        get-products.rps.js           # RPS: GET /products
        create-order-endpoint.rps.js   # RPS: POST /orders
      
      tps/
        login-flow.tps.js             # TPS: flujo login
        checkout-flow.tps.js          # TPS: flujo checkout
        payment-flow.tps.js           # TPS: flujo pago
            
      stress/
        api-stress.js                 # Encontrar límites
      
      soak/
        api-soak.js                   # Resistencia prolongada
```

---

## Instalación y configuración

### Instalar k6

**macOS (Homebrew)**:
```bash
brew install k6
```

**Linux (Debian/Ubuntu)**:
```bash
sudo apt-get update
sudo apt-get install k6
```

**Windows (Chocolatey)**:
```bash
choco install k6
```

### Verificar instalación

```bash
k6 version
```

### Configurar variables de entorno

Crea un archivo `.env.local` en la raíz del proyecto (No commitear):

```bash
BASE_URL=http://localhost:8000
TEST_ENV=local
AUTH_USER=test.user@example.com
AUTH_PASSWORD=ChangeMe123!
```

---

## Ejecución de pruebas

### Comando base

```bash
k6 run [opciones] [script.js]
```

### Variables de entorno comunes

```bash
# URL base de la API
-e BASE_URL=http://localhost:8000

# Ambiente
-e TEST_ENV=local

# Credenciales
-e AUTH_USER=test@example.com
-e AUTH_PASSWORD=SecurePass123!

# Rate/TPS
-e RATE=100
-e TPS=20

# Duración
-e DURATION=5m

# VUs (Virtual Users)
-e VUS=10
-e MAX_VUS=100
```

### Opciones comunes de k6

```bash
# Verbosidad
-v, --verbose                 # Más detalles
--logformat json              # Logs en JSON

# Output
--summary-export=result.json  # Exportar resumen

# Lienzo de control
--address 0.0.0.0:6565        # Iniciar web UI (experimental)
```

### Ejemplo: Smoke test

```bash
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e TEST_ENV=local \
  tests/performance/k6/smoke/api-smoke.js
```

---

## RPS - Requests Per Second

### Uso

Mide capacidad técnica de un endpoint aislado.

**Cuándo usarla:**
- Benchmark de endpoint específico
- Detectar cuello de botella
- Regresión de performance
- Comparar versiones

**No usarla cuando:**
- Quieras medir flujo de negocio completo → usa TPS

### Estructura

```javascript
import { getConfig } from '../config/environments.js';
import { buildThresholds } from '../config/thresholds.js';

const cfg = getConfig();

export const options = {
  scenarios: {
    get_users_rps: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 20),      // Requests por segundo
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 60),
    },
  },
  thresholds: buildThresholds({
    'http_req_duration{name:get-users}': ['p(95)<500'],
  }),
};

export default function () {
  // Una iteración = 1 request
}
```

### Ejecutar RPS test

```bash
# Baseline
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e RATE=50 \
  -e DURATION=2m \
  tests/performance/k6/rps/get-users.rps.js

# Stress
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e RATE=500 \
  -e DURATION=5m \
  tests/performance/k6/rps/get-users.rps.js
```

### Interpretar resultados

```text
✓ http_req_duration....................: avg=145.23ms, p(95)=312.45ms, p(99)=891.20ms
✓ http_req_failed.......................: 0.00% ✓
✓ http_reqs.............................: 6000/s ✓
```

- Pasó: p(95) está dentro del threshold
- Pasó: 0% de errores (< 1%)
- Información: ~6000 requests en total

---

## TPS - Transactions Per Second

### Uso

Mide capacidad de negocio en flujos completos.

**Cuándo usarla:**
- Medir flujo de usuario real
- Capacidad de transacciones de negocio
- Validar flujo bajo carga
- Aceptancia de SLA de negocio

**No usarla cuando:**
- Solo quieras medir un endpoint aislado → usa RPS

### Estructura

```javascript
import { getConfig } from '../config/environments.js';
import { tpsThresholds } from '../config/thresholds.js';
import { recordTransaction } from '../shared/metrics.js';

const cfg = getConfig();

export const options = {
  scenarios: {
    login_tps: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.TPS || 8),         // Transacciones por segundo
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 60),
    },
  },
  thresholds: tpsThresholds(Number(__ENV.TPS || 8)),
};

export default function () {
  const startedAt = Date.now();
  
  // Múltiples requests = 1 transacción
  // (login, obtener perfil, listar productos, etc.)
  
  recordTransaction('login-flow', Date.now() - startedAt, success);
}
```

### Ejecutar TPS test

```bash
# Baseline
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e TPS=10 \
  -e DURATION=3m \
  tests/performance/k6/tps/checkout-flow.tps.js

# Bajo carga
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e TPS=50 \
  -e DURATION=5m \
  tests/performance/k6/tps/checkout-flow.tps.js
```

### Interpretar resultados

```text
✓ transaction_success_rate..............: 98.50% ✓
✓ transaction_duration..................: avg=834ms, p(95)=1200ms
✓ iterations............................: 600/s ✓
```

- Pasó: 98.5% de transacciones exitosas (> 98%)
- Información: p95 de transacción es 1.2 segundos
- Información: 600 iteraciones (600 TPS)

---

## Smoke - Validación rápida

### Uso

Valida que scripts, ambiente y endpoints funcionen antes de pruebas pesadas.

**Para:**
- Verificar que API responde
- Validar credenciales
- Confirmar variables de entorno
- Detectar errores en scripts antes de ejecutar pruebas largas

**Duración:** 10-30 segundos  
**VUs:** 1-5  
**Requests:** Muy pocas

### Estructura

```javascript
export const options = {
  vus: Number(__ENV.VUS || 1),
  iterations: Number(__ENV.ITERATIONS || 5),
  thresholds: buildThresholds({
    http_req_duration: ['p(95)<1000'],
  }),
};

export default function () {
  // Validar rutas health, login, etc.
}
```

### Ejecutar smoke test

```bash
# Rápido
k6 run \
  -e BASE_URL=http://localhost:8000 \
  tests/performance/k6/smoke/api-smoke.js

# Detallado
k6 run -v \
  -e BASE_URL=http://localhost:8000 \
  tests/performance/k6/smoke/api-smoke.js
```

---

## Stress - Encontrar límites

### Uso

Aumenta carga progresivamente para encontrar el punto de degradación.

**Para:**
- Identificar límite máximo del sistema
- Encontrar RPS/TPS crítico
- Ver cómo falla el sistema
- Validar autoscaling

**Duración:** 10-20 minutos  
**Carga:** Incremental (ramping-arrival-rate)

### Estructura

```javascript
export const options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-arrival-rate',
      startRate: Number(__ENV.START_RATE || 10),
      stages: [
        { target: 100, duration: '2m' },  // 10 → 100
        { target: 200, duration: '2m' },  // 100 → 200
        { target: 300, duration: '2m' },  // 200 → 300
        { target: 0, duration: '1m' },    // Cooldown
      ],
    },
  },
};
```

### Ejecutar stress test

```bash
k6 run \
  -e BASE_URL=http://localhost:8000 \
  tests/performance/k6/stress/api-stress.js
```

### Interpretar resultados

```text
✓ http_req_failed: 0% @ 100 RPS
✗ http_req_failed: 2.1% @ 250 RPS    # Empezó a fallar aquí
✗ http_req_failed: 8.5% @ 300 RPS    # Peor aquí
```

El sistema comienza a degradarse alrededor de 250 RPS.

---

## Soak - Resistencia a largo plazo

### Uso

Carga sostenida durante horas para detectar problemas progresivos.

**Para:**
- Memory leaks
- Saturación de conexiones
- Degradación de latencia en tiempo
- Problemas de cache
- Acumulación en colas
- Inestabilidad a largo plazo

**Duración:** 30 min - 4+ horas  
**Carga:** Estable y moderada

### Estructura

```javascript
export const options = {
  scenarios: {
    soak_test: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 8),
      duration: __ENV.DURATION || '60m',  // Larga duración
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 100),
    },
  },
};
```

### Ejecutar soak test

```bash
# 30 minutos
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e RATE=10 \
  -e DURATION=30m \
  tests/performance/k6/soak/api-soak.js

# 2 horas
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e RATE=10 \
  -e DURATION=120m \
  tests/performance/k6/soak/api-soak.js
```

### Monitorear resultados

```bash
# Exportar resultados para análisis
k6 run \
  --summary-export=soak-results.json \
  tests/performance/k6/soak/api-soak.js
```

---

## Shared - Código reutilizable

### Archivos incluidos

#### `auth.js`
Autenticación centralizada.

```javascript
import { login, getAuthToken, authHeaders } from '../shared/auth.js';

// En tus tests:
const token = getAuthToken();
const headers = authHeaders();  // { Authorization: Bearer ... }
```

#### `http-client.js`
Cliente HTTP con manejo de errores y métricas.

```javascript
import { request, checkResponse, jsonBody } from '../shared/http-client.js';

const response = request('POST', `${cfg.baseUrl}/orders`, jsonBody(payload), {
  headers: authHeaders(),
  tags: { name: 'create-order' },
});

checkResponse(response, 'create-order', 201);
```

#### `metrics.js`
Métricas custom para RPS y TPS.

```javascript
import { recordTransaction, recordResponse } from '../shared/metrics.js';

recordResponse(response, { endpoint: 'get-users' });
recordTransaction('login-flow', durationMs, success);
```

---

## Config - Configuración centralizada

### `environments.js`

Define URLs y credenciales por ambiente.

```javascript
import { getConfig } from '../config/environments.js';

const cfg = getConfig();
// cfg.baseUrl  = http://localhost:8000
// cfg.username = test.user@example.com
// cfg.password = ChangeMe123!
```

Sobrescribe con variables de entorno:

```bash
-e BASE_URL=https://api-prod.midominio.com
-e TEST_ENV=prod
```

### `thresholds.js`

Thresholds reutilizables.

```javascript
import { rpsThresholds, tpsThresholds } from '../config/thresholds.js';

export const options = {
  thresholds: rpsThresholds(100),  // 100 RPS
};
```

---

## Data - Datos de prueba

### `users.csv`

Usuarios para pruebas.

```csv
id,email,password
1,test.user1@example.com,Password123!
2,test.user2@example.com,Password123!
```

Leer en scripts:

```javascript
import { SharedArray } from 'k6/data';

const users = new SharedArray('users', function () {
  const raw = open('../data/users.csv').trim().split('\n');
  return raw.slice(1).map(line => {
    const [id, email, password] = line.split(',');
    return { id, email, password };
  });
});

export default function () {
  const user = users[Math.floor(Math.random() * users.length)];
  // usar user
}
```

### `products.json`

Productos para pruebas.

```json
[
  { "id": "prod-1001", "quantity": 1 },
  { "id": "prod-1002", "quantity": 2 }
]
```

Leer en scripts:

```javascript
const products = new SharedArray('products', () => 
  JSON.parse(open('../data/products.json'))
);
```

---

## Troubleshooting

### Error: "Cannot find module"

```
ERRO[0000] GoError: Init context failed:
  Error at line 1 of ./tests/performance/k6/rps/get-users.rps.js: 
  Cannot find module '../config/environments.js'
```

**Solución:** Verifica la ruta relativa desde el script. Las rutas deben ser relativas al script, no a la raíz del proyecto.

```javascript
// Correcto:
import { getConfig } from '../config/environments.js';

// Incorrecto:
import { getConfig } from 'config/environments.js';
```

### Error: "Authentication failed"

```
✗ check: login failed
  The username/password is wrong
```

**Solución:** Verifica credenciales en variables de entorno:

```bash
-e AUTH_USER=test.user@example.com
-e AUTH_PASSWORD=CorrectPassword123!
```

### Error: "Connection refused"

```
E[0000] Connection refused
```

**Solución:** Verifica que la API está corriendo en BASE_URL:

```bash
k6 run -e BASE_URL=http://localhost:8000 ...
```

### Test falla por threshold

```
ERRO[0001] Threshold "http_req_failed: rate<0.01" has failed
```

**Solución:** 
- El error rate está por encima del 1%
- Verifica que la API responde correctamente
- Aumenta timeout o revisa requests que fallan

```bash
k6 run -v ...  # -v para detalles
```

### Performance lenta

```text
✗ http_req_duration: p(95)=2500ms (expected < 500ms)
```

**Solución:**
- La API es lenta
- Red tiene latencia alta
- Base de datos está saturada

Verifica directamente:

```bash
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Out of memory

```
panic: signal: killed
```

**Solución:** Reduce VUs o duration:

```bash
k6 run \
  -e MAX_VUS=20 \
  -e DURATION=2m \
  ...
```

---

## Buenas prácticas

1. **Siempre ejecuta smoke primero:** Valida ambiente antes de pruebas pesadas
2. **Usa variables de entorno:** Reutiliza scripts entre ambientes
3. **Define thresholds claros:** Automatiza decisión pass/fail
4. **Centraliza código:** No repitas lógica, usa `shared/`
5. **Monitorea p95/p99:** No confíes solo en promedios
6. **Incrementa carga gradualmente:** Empieza bajo, sube lentamente
7. **Revisa logs en verbose:** `-v` cuando algo falla
8. **Exporta resultados:** `--summary-export` para análisis posterior

---

## Comandos de referencia rápida

```bash
# Smoke test
k6 run tests/performance/k6/smoke/api-smoke.js

# RPS baseline
k6 run -e RATE=50 -e DURATION=2m tests/performance/k6/rps/get-users.rps.js

# TPS bajo carga
k6 run -e TPS=20 -e DURATION=5m tests/performance/k6/tps/checkout-flow.tps.js

# Stress test
k6 run tests/performance/k6/stress/api-stress.js

# Soak 30 min
k6 run -e DURATION=30m tests/performance/k6/soak/api-soak.js

# Verbose + export
k6 run -v --summary-export=result.json tests/performance/k6/rps/get-users.rps.js
```

---

**Última actualización:** mayo 2026  
**Versión k6 recomendada:** 0.45+  
**Autores:** Arify Labs Performance Team
