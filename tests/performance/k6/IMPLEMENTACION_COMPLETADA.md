# ✅ COMPLETADO: Suite de Tests de Performance K6

## 📋 Resumen Ejecutivo

Se completó la suite completa de tests de performance parametrizable para evaluar los 3 controladores principales:
- **BianExampleController** (2 endpoints)
- **NoBianExampleController** (1 endpoint)  
- **NoBianExampleRedisController** (1 endpoint)

**Todos los tests son:**
- ✅ Parametrizables (URL, VUs, duración vía CLI)
- ✅ Locales (http://127.0.0.1:8000)
- ✅ Sin datos sensibles
- ✅ Listos para ejecutar

---

## 📁 Estructura Completada

```
tests/performance/k6/
│
├── 📄 PERFORMANCE_TESTS_README.md    ← Guía completa
├── 📄 QUICK_START.md                 ← Comandos listos para copiar
├── 📄 run-tests.sh                   ← Script wrapper (bash)
│
├── 🔧 config/
│   ├── environments.js               ✅ Actualizado (parametrizable)
│   └── thresholds.js                 ✅ Actualizado (smoke/stress/soak)
│
├── 📊 data/
│   └── example-requests.json         ✅ Datos de prueba (sin secretos)
│
├── 🔌 shared/
│   ├── http-client.js                ✅ Cliente HTTP base
│   ├── request-builder.js            ✅ NUEVO - Constructores de requests
│   └── metrics.js                    ✅ Existente
│
├── 📈 rps/ (Requests Per Second - 100+ RPS esperados)
│   ├── bian-example.rps.js           ✅ NUEVO
│   ├── no-bian-example.rps.js        ✅ NUEVO
│   └── no-bian-redis.rps.js          ✅ NUEVO
│
├── 🔥 smoke/ (Validación rápida - 10-20s)
│   ├── basic-health-check.smoke.js   ✅ NUEVO
│   └── endpoints-validation.smoke.js ✅ NUEVO
│
├── 💥 stress/ (Encontrar límites - 60s)
│   └── concurrent-load.stress.js     ✅ NUEVO
│
└── 🧊 soak/ (Resistencia a largo plazo - 300s)
    └── long-running.soak.js          ✅ NUEVO
```

---

## 🎯 Tipos de Tests Implementados

### 1️⃣ SMOKE Tests (🔥 Rápido - 10-20 segundos)

**Propósito:** Validación inicial rápida

| Archivo | Duración | VUs | Objetivo |
|---------|----------|-----|----------|
| basic-health-check.smoke.js | 10s | 1 | Disponibilidad del servidor |
| endpoints-validation.smoke.js | 20s | 5 | Validar 3 endpoints + latencia |

**Comandos:**
```bash
k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000
k6 run smoke/endpoints-validation.smoke.js --env BASE_URL=http://127.0.0.1:8000 --vus 5
```

---

### 2️⃣ RPS Tests (📈 Rendimiento - 30 segundos cada)

**Propósito:** Medir requests por segundo que soporta cada endpoint

| Controller | Endpoint | Expected RPS | Archivo |
|-----------|----------|--------------|---------|
| BianExample | POST /{id}/create + POST /new/create | 100+ | bian-example.rps.js |
| NoBianExample | POST /{id}/create | 100+ | no-bian-example.rps.js |
| NoBianExampleRedis | POST /{id}/create-redis | 150+ | no-bian-redis.rps.js |

**Comandos:**
```bash
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
k6 run rps/no-bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
k6 run rps/no-bian-redis.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 75 --duration 30s
```

---

### 3️⃣ STRESS Test (💥 Límites - 60 segundos)

**Propósito:** Encontrar punto de ruptura

| Métrica | Umbral |
|---------|--------|
| Error Rate | < 5% |
| p95 Latencia | < 1500ms |
| p99 Latencia | < 3000ms |
| Carga máxima | 200 VUs |

**Comando:**
```bash
k6 run stress/concurrent-load.stress.js --env BASE_URL=http://127.0.0.1:8000 --vus 200 --duration 60s
```

---

### 4️⃣ SOAK Test (🧊 Resistencia - 300 segundos)

**Propósito:** Validar estabilidad a largo plazo

| Métrica | Duración | VUs |
|---------|----------|-----|
| Mantener carga | 3 minutos | 30 |
| Error Rate | < 2% | - |
| p95 Latencia | < 800ms | - |

**Comando:**
```bash
k6 run soak/long-running.soak.js --env BASE_URL=http://127.0.0.1:8000 --vus 30 --duration 300s
```

---

## 🔧 Parámetros Disponibles

Todos los tests aceptan parámetros vía `--env`:

```bash
# URL Base (REQUERIDO si no es localhost:8000)
--env BASE_URL=http://127.0.0.1:8000

# Virtual Users  
--vus 50

# Duración
--duration 30s

# Headers opcionales
--env DEVICE_ID=mobile-test-device
--env CUSTOMER_ID=12345
--env CHANNEL_ID=WEB
```

### Ejemplo con parámetros personalizados
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env CUSTOMER_ID=99999 \
  --env CHANNEL_ID=MOBILE \
  --vus 100 \
  --duration 60s
```

---

## 🚀 Flujo Recomendado

1. **Smoke** (5 min) → Valida disponibilidad
2. **RPS x3** (15 min) → Mide capacidad individual
3. **Stress** (5 min) → Identifica límites
4. **Soak** (10 min) → Valida estabilidad

**Tiempo total:** ~35-40 minutos

---

## 📊 Interpretación de Resultados

### Salida Exitosa ✅
```
✓ [✓] http_reqs: 3000+ (target 100 achieved)
✓ [✓] http_req_failed: 0.00% (< 1%)
✓ [✓] http_req_duration: p(95)=450ms (< 500ms)
✓ [✓] checks: 99.8% (> 99%)

✓ Test passed
```

### Salida con Problemas ❌
```
✗ [✗] http_reqs: 45 (target 100 failed)
✗ [✗] http_req_failed: 5.2% (< 1% failed)
✗ [✗] http_req_duration: p(95)=2300ms (< 500ms failed)

✗ 3 thresholds failed
```

**Acciones:**
- ↓ RPS bajo: Aumentar VUs o investigar server
- ↑ Errores: Revisar logs del servidor
- ↑ Latencia: Cuello de botella en DB o red

---

## 📝 Archivos Clave

### Configuración Central
- **config/environments.js** - Parámetros por ambiente
- **config/thresholds.js** - Umbrales de éxito por tipo de test

### Constructores de Requests
- **shared/request-builder.js** - Funciones para cada endpoint:
  - `bianExampleCreate()`
  - `bianExampleCreateSecure()`
  - `noBianExampleCreate()`
  - `noBianExampleRedisCreate()`

### Datos
- **data/example-requests.json** - Datos sin secretos (customer_ids, devices, etc)

---

## ⚠️ Notas Importantes

- ✅ **Todo es LOCAL** (http://127.0.0.1:8000)
- ✅ **Sin secretos** en datos de prueba
- ✅ **Sin autenticación requerida** (excepto /new/create que acepta sin token)
- ✅ **Parametrizable** - Enviar URL, VUs, duración, headers vía CLI
- ⚠️ **TPS Tests NO incluidos** (como solicitaste - en tps/ están pero sin usar)

---

## 🎯 Headers Requeridos en Requests

Todos los endpoints esperan estos headers (enviados automáticamente):

```
device_identifier: string         # ID del dispositivo (default: mobile-test-device)
message_identifier: string        # ID único del mensaje
channel_identifier: string        # Canal: WEB, MOBILE, API, INTERNAL
Content-Type: application/json
```

---

## 📚 Documentación

- **PERFORMANCE_TESTS_README.md** - Guía completa (80+ líneas)
- **QUICK_START.md** - Comandos listos para copiar/pegar
- **Este archivo** - Resumen ejecutivo

---

## ✨ Características Implementadas

✅ Todos los 3 controladores cubiertos  
✅ 4 tipos de tests (smoke, rps, stress, soak)  
✅ 2 + 1 + 1 = 4 endpoints probados  
✅ Parámetros enviados por CLI (URL, VUs, duración)  
✅ Headers requeridos incluidos automáticamente  
✅ Datos de prueba sin secretos  
✅ Umbrales configurables por tipo de test  
✅ Scripts listos para ejecutar  
✅ Documentación completa  
✅ TPS Tests NO incluidos (como solicitaste)  
✅ TODO ES LOCAL Y ESTÁTICO

---

**¿LISTO PARA EMPEZAR?**

Revisa: **QUICK_START.md**  
Comando más rápido: `k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000`

---

**Fecha:** 30/05/2026  
**Estado:** ✅ COMPLETADO Y LISTO PARA USAR
