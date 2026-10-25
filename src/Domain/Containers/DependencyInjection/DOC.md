# Dependency Injection Container

Este contenedor centraliza la composición de Runtime e Infrastructure sin acoplarlas a FastAPI ni a un proveedor externo de DI.

## Problema que resuelve

Sin un contenedor, cada controller, nodo o caso de uso tendría que construir sus dependencias directamente. Eso provoca clientes HTTP/Redis/Bedrock repetidos, pools de conexión innecesarios y grafos LangGraph recompilados por request.

El contenedor define un lifetime explícito para cada servicio y permite reutilizar recursos seguros para concurrencia.

## Fachada pública

La fachada es `CoreServices`. Las APIs existentes se mantienen compatibles.

### Singleton por implementación

```python
Services.add_singleton_dependency(IRuntimeGraphPort, IncidentGraphPort)
graph = Services.get_dependency(IRuntimeGraphPort)
```

La implementación se construye de forma lazy en la primera resolución y se reutiliza durante toda la aplicación.

Use este método únicamente cuando el constructor no necesite parámetros.

### Singleton por instancia

```python
connector = HttpClientConnector(timeout_sec=25)
Services.add_singleton_instance(connector)

same_connector = Services.get_instance(HttpClientConnector)
```

Registra una instancia ya construida. Es apropiado para clientes con pools de conexiones o recursos que deben cerrarse durante el shutdown.

### Singleton por factory

```python
Services.add_singleton_factory(IRuntimeGraphPort, build_compiled_incident_graph)
graph = Services.get_dependency(IRuntimeGraphPort)
```

La factory se ejecuta una sola vez y de forma segura ante resoluciones concurrentes. Es la opción recomendada para un grafo LangGraph compilado porque permite inyectar checkpointer, nodos y contratos antes de compilarlo.

### Transient por implementación

```python
Services.add_transient_dependency(AttendIncidentUsecase, AttendIncidentUsecase)
usecase = Services.get_dependency(AttendIncidentUsecase)
```

Crea una instancia nueva en cada resolución. Úselo para objetos sin estado compartido y de vida corta.

### Transient por factory

```python
Services.add_transient_factory(
    AttendIncidentUsecase,
    lambda: AttendIncidentUsecase(Services.get_dependency(IRuntimeGraphPort)),
)
```

Útil cuando un transient necesita dependencias ya registradas.

## Lifetimes recomendados

| Servicio | Lifetime |
|---|---|
| Grafo LangGraph compilado | Singleton factory |
| Checkpointer durable | Singleton instance/factory |
| `HttpClientConnector` | Singleton instance |
| Cliente Redis | Singleton instance |
| Clientes Bedrock | Singleton instance/factory |
| Configuración | Singleton instance |
| Caso de uso sin estado | Transient |
| Request/response adapters | Por request, no registrar |
| Estado de conversación | Persistido por checkpointer, no singleton |

## LangGraph

El grafo es reutilizable si no guarda datos de una conversación en atributos mutables. Los datos variables viajan en cada llamada:

```python
await graph.ainvoke(
    graph_input,
    {"configurable": {"thread_id": request.thread_id}},
)
```

El `thread_id`, `correlation_id`, contexto de usuario y payload de request nunca deben guardarse en el singleton del grafo.

## Relación con FastAPI

FastAPI puede usar `Depends` para dependencias de transporte. Runtime e Infrastructure se resuelven a través de `CoreServices` desde Presentation. Runtime no debe importar `fastapi.Depends`.

## Shutdown

Los recursos singleton que mantienen conexiones deben cerrarse en el `lifespan` de la aplicación, por ejemplo:

```python
await Services.get_instance(HttpClientConnector).close()
await Services.get_instance(RedisMemoryClient).close()
```
