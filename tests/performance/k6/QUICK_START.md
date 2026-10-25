# QUICK START - Comandos para ejecutar ahora

## ⚠️ Paso 1: Asegúrate que el servidor está corriendo

```bash
# Desde carpeta src/
cd /Users/vcaxi/Desktop/vcaxi/mio/business-api-3.0-/src

# Inicia el servidor
uvicorn Presentation.app:app --reload

# Espera el mensaje: Uvicorn running on http://127.0.0.1:8000
```

## 📁 Paso 2: Abre otra terminal en la carpeta k6

```bash
cd /Users/vcaxi/Desktop/vcaxi/mio/business-api-3.0-/tests/performance/k6
```

## 🚀 Paso 3: Ejecuta los tests (elige uno)

### Opción A: SMOKE (10 segundos - Rápido ✨)
```bash
k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000
```

### Opción B: Validación de Endpoints (20 segundos)
```bash
k6 run smoke/endpoints-validation.smoke.js --env BASE_URL=http://127.0.0.1:8000 --vus 5
```

### Opción C: RPS - BianExampleController (30 segundos)
```bash
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
```

### Opción D: RPS - NoBianExampleController (30 segundos)
```bash
k6 run rps/no-bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
```

### Opción E: RPS - NoBianExampleRedisController (30 segundos)
```bash
k6 run rps/no-bian-redis.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 75 --duration 30s
```

### Opción F: STRESS (60 segundos - Encuentra límites 💪)
```bash
k6 run stress/concurrent-load.stress.js --env BASE_URL=http://127.0.0.1:8000 --vus 200 --duration 60s
```

### Opción G: SOAK (300 segundos = 5 minutos ☕)
```bash
k6 run soak/long-running.soak.js --env BASE_URL=http://127.0.0.1:8000 --vus 30 --duration 300s
```

---

## 📊 Ejecución COMPLETA (30-40 minutos)

Ejecuta todos los tests en secuencia:

```bash
# SMOKE
k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000

# RPS Tests
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
k6 run rps/no-bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s
k6 run rps/no-bian-redis.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 75 --duration 30s

# STRESS
k6 run stress/concurrent-load.stress.js --env BASE_URL=http://127.0.0.1:8000 --vus 200 --duration 60s

# SOAK
k6 run soak/long-running.soak.js --env BASE_URL=http://127.0.0.1:8000 --vus 30 --duration 300s
```

---

## 🔧 Personalización de parámetros

### Cambiar URL
```bash
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000
```

### Cambiar Virtual Users
```bash
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 100
```

### Cambiar Duración
```bash
k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 60s
```

### Cambiar Customer ID
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env CUSTOMER_ID=99999 \
  --vus 50 --duration 30s
```

### Cambiar Channel
```bash
k6 run rps/bian-example.rps.js \
  --env BASE_URL=http://127.0.0.1:8000 \
  --env CHANNEL_ID=MOBILE \
  --vus 50 --duration 30s
```

---

## ✅ Métricas a observar

Después de ejecutar cada test, busca:

- ✅ `http_reqs: XXX (✓)` - Alcanzó objetivo de requests
- ✅ `http_req_failed: X.XX%` - Porcentaje de fallos (< 1% es bueno)
- ✅ `http_req_duration: p(95)=XXms` - Latencia percentil 95
- ✅ `checks: X.XX% (✓)` - Validaciones exitosas (> 99% es bueno)

---

## 🐛 Si algo falla

### Error de conexión
```
Error: Failed to connect to http://127.0.0.1:8000
```
→ Verifica que el servidor está corriendo (uvicorn)

### Timeouts
```
Error: Request timeout exceeded
```
→ Servidor lento o sobrecargado. Reduce --vus

### Headers incorrectos
```
422 Unprocessable Entity
```
→ Revisa que device_identifier, message_identifier, channel_identifier se envían correctamente

### Sin datos de caché
```
204 No Content
```
→ Normal en algunas iteraciones. El endpoint está funcionando.

---

## 📝 Notas

- **URL Local:** Todos los tests usan `http://127.0.0.1:8000` (editable con `--env BASE_URL`)
- **Sin autenticación requerida** excepto endpoint `POST /new/create` (que acepta sin token)
- **Sin datos sensibles** en `data/` (archivos de prueba public)
- **TPS Tests:** NO incluidos (como solicitaste)
- **Estático:** Todo es local, no se conecta a prod ni dev

---

**¡Listo! Ejecuta el comando que prefieras y observa los resultados.** 🎯
