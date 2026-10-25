# HttpClient Memory Queue - Optimizaciones Implementadas

## Resumen
Se ha extendido la funcionalidad del `HttpClientInfrastructure` con un sistema de captura de eventos en memoria optimizado que solo se activa cuando es necesario.

## 1.5. How to use HTTP Client Builder (soon: pip install arify-httpclient)
1. Ejemplo de Uso Básico
   ```python
   import asyncio
   from Infrastructure.HttpClientInfrastrucuture.HttpClientInfrastructure import HttpClientInfrastructure

   async def main():
      # Instanciar el builder con timeout de 15s (por defecto).
      client = HttpClientInfrastructure(timeout=15)

      # Construir una petición GET a "https://jsonplaceholder.typicode.com/todos/1".
      response = await (client
         .http("https://jsonplaceholder.typicode.com")
         .endpoint("todos/1")
         .get()
      )

      print("Status code:", response.StatusCode)
      print("Contenido:", response.Content)

      # Cerrar la conexión cuando no se use más.
      await client.close()

   asyncio.run(main())
2. Realizar una petición GET simple
   ```python
   response = await (
      client
         .http("https://api.example.com")
         .endpoint("users")
         .get()
   )
3. Agregar parámetros y query string
   ```python
   response = await (
      client
         .http("https://api.example.com")
         .endpoint("search")
         .param("sort", "desc")         # Parámetro enviado en "params="
         .query("filter", "active")     # Parámetro de query string "?filter=active"
         .get()
   )
4. Enviar múltiples cabeceras
   ```python
   response = await (
      client
         .http("https://api.example.com")
         .endpoint("batchHeaders")
         .headers({"X-Request-ID": "abc123", "X-Custom-Token": "xyz789"})
         .get()
   )
5. Usar cabeceras personalizadas
   ```python
   response = await (
      client
         .http("https://api.example.com")
         .endpoint("profile")
         .header("X-Client-Version", "1.0.0")
         .header("X-Device", "Desktop")
         .get()
   )
6. Autenticación con Bearer token
   ```python
   response = await (
      client
         .http("https://api.example.com")
         .endpoint("reports")
         .authorization("Bearer", "MiTokenSecreto123")
         .get()
   )
7. Enviar datos en el cuerpo (POST/PUT)
   ```python
   payload = {
      "title": "Nuevo Item",
      "description": "Creando un item via API"
   }

   response = await (
      client
         .http("https://api.example.com")
         .endpoint("items")
         .post(body=payload)
   )

## Optimizaciones Clave

### 1. **Activación Condicional**
- La captura de eventos solo se ejecuta si se llama `with_memory_queue()`
- Flag `__memory_enabled` evita verificaciones innecesarias en cada request
- Cero overhead cuando no se usa memory queue

### 2. **Serialización Optimizada**
- Método `_serialize_payload()` con manejo eficiente de tipos
- Usa `json.dumps()` con separadores compactos para reducir tamaño
- Manejo seguro de errores sin excepciones costosas

### 3. **Uso de try_push()**
- Evita bloqueos usando `try_push()` en lugar de `push_async()`
- No bloquea el flujo principal si la cola está llena
- Mejor rendimiento en escenarios de alta concurrencia

### 4. **Gestión de Memoria Eficiente**
- Reutilización de `identity` para request/response del mismo call
- Campos opcionales con valores por defecto para reducir memoria
- Método `reset_memory_state()` para limpiar estado entre operaciones

### 5. **Timestamps Optimizados**
- `RequestDatetime` se captura una sola vez y se reutiliza
- `ResponseDatetime` se genera solo cuando es necesario
- Reduce llamadas a `datetime.utcnow()`

## Uso Recomendado

### Para Captura de Eventos
```python
client = HttpClientInfrastructure()
response = await (client
    .http("https://api.example.com")
    .endpoint("users")
    .with_memory_queue(queue, "User.Create.execute", "user_ops")
    .post(user_data))
```

### Para Máximo Rendimiento (sin captura)
```python
client = HttpClientInfrastructure()
response = await (client
    .http("https://api.example.com")
    .endpoint("health")
    .get())  # Sin with_memory_queue() = sin overhead
```

### Para Reutilización de Cliente
```python
# Operación con memory
await client.with_memory_queue(queue, "Op1").get()

# Reset para nueva operación sin memory
client.reset_memory_state()

# Operación sin memory (más rápida)
await client.endpoint("health").get()
```

## Beneficios de Rendimiento

1. **Cero Overhead**: Sin memory queue, no hay impacto en rendimiento
2. **No Bloqueos**: `try_push()` nunca bloquea el hilo principal
3. **Memoria Eficiente**: Serialización optimizada y limpieza de estado
4. **Reutilización**: Un cliente puede manejar múltiples operaciones
5. **Escalabilidad**: Funciona bien bajo alta concurrencia

## Consideraciones

- La cola tiene capacidad limitada (configurable)
- Si la cola está llena, los eventos se descartan silenciosamente
- Para debugging crítico, considerar usar `push_async()` con timeout
- El `reset_memory_state()` es opcional pero recomendado para reutilización