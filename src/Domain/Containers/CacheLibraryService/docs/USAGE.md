# CacheLibraryService - Guia de uso rapido

<div align="right"><sub>ARIFY Labs</sub></div>

## Proposito

`CacheLibraryService` es una libreria compacta para dos escenarios clave:

- cache de datos: mejora latencia y reduce llamadas a origen con comportamiento fail-open por defecto;
- idempotencia: protege operaciones criticas con reservas atomicas, ownership y modo fail-closed mediante `ensure_provider_available()`.

La regla practica es simple: si la cache solo acelera, se deja pasar; si la cache decide si una operacion puede ejecutarse, se obliga disponibilidad del provider.

## Setup

```python
from Domain.Containers.CacheLibraryService.CacheLibraryService import CacheLibraryService
from Domain.Containers.CacheLibraryService.Internals.MemoryCacheInfrastructure import MemoryCacheInfrastructure

provider = MemoryCacheInfrastructure()
cache = CacheLibraryService(provider)
```

En un microservicio real, el provider concreto (`ICacheInfrastructure`) debe venir por DI desde Infrastructure.

## API real

```python
builder = cache.for_key("cfg-11-currencies")

builder.use_strategy(...)                      # CacheStrategy
builder.with_ttl(ttl, ttl_jitter=timedelta()) # optional
builder.with_owner(owner_token)               # optional, recomendado para idempotencia
builder.ensure_provider_available(required=True) # optional, default=False

await builder.resolve_async(loader=None, deserializer=None)
await builder.put_async(value=None)
await builder.remove_async()
await builder.exists_async()

await builder.get_created_async(deserializer=None, required=False)
await builder.get_status_async(required=False)
await builder.try_reserve_async()
await builder.try_complete_async(value=None)
```

Notas:

- El metodo es `for_key`, no `ForKey`.
- No se usa `CancellationToken` en la firma publica.
- `resolve_async` acepta un `loader` async sin argumentos.
- Si se espera recuperar un modelo/adapter, `resolve_async` debe usar `deserializer` explicito.

## Disponibilidad del provider (bloquear o dejar pasar)

Si necesitas bloquear ante caida del provider, usa `ensure_provider_available()`.

Comportamiento real:

- Por defecto, la libreria usa fail-open: si el provider falla o vence timeout (0.5s), retorna fallback (`None` o `False`) y el flujo continua.
- Casos bloqueantes (strict): `CACHE_ONLY_REQUIRED`, `exists_async`, o cualquier operacion cuando activas `ensure_provider_available()`.
  - En estos casos, si el provider cae o no responde, se propaga excepcion (`RuntimeError`).

Resumen practico:

- Si quieres dejar pasar ante caidas del provider: usa estrategias normales (`CACHE_ONLY`, `CACHE_THEN_SOURCE`, `CACHE_THEN_SOURCE_AND_STORE`, `SOURCE_AND_STORE`, `STORE_ONLY`, `STORE_ONLY_OR_RESERVE`).
- Si quieres bloquear ante caidas del provider: usa `CACHE_ONLY_REQUIRED`, `exists_async` o activa `ensure_provider_available()`.

## Clasificacion de estrategias (cache de datos vs idempotencia/estado)

### 1) Estrategias con source (cacheo de datos con fallback a origen)

Estas estrategias pueden ejecutar `loader` y son para lectura/refresh de datos:

- `CACHE_THEN_SOURCE`
- `CACHE_THEN_SOURCE_AND_STORE`
- `SOURCE_AND_STORE`

Regla practica:

- Si necesitas traer datos desde un origen cuando no hay cache, usa este grupo.
- Si tambien quieres persistir el resultado en cache, usa `CACHE_THEN_SOURCE_AND_STORE` o `SOURCE_AND_STORE`.

### 2) Estrategias sin source (solo cache/estado/idempotencia)

Estas estrategias no ejecutan `loader`; trabajan solo con estado en cache:

- `CACHE_ONLY`
- `CACHE_ONLY_REQUIRED`
- `CACHE_ONLY_THEN_CLOSE`
- `STORE_ONLY`
- `STORE_ONLY_OR_RESERVE`

Regla practica:

- Si estas implementando idempotencia, reservas o validaciones por estado, usa este grupo.
- Para idempotencia en produccion, combinar con `ensure_provider_available()` en operaciones criticas.

## Primitivas de idempotencia recomendadas

Para flujos de alta concurrencia, evita secuencias manuales (read + reserve + write) repartidas en el caso de uso.
Usa estas primitivas de `CacheLibraryService`:

- `try_reserve_async()`: intenta crear estado `started` de forma atomica.
- `try_complete_async(value)`: completa `started -> created` de forma condicional.
- `get_created_async(...)`: recupera resultado final solo si estado es `created`.
- `get_status_async()`: permite inspeccionar estado (`started|created|closed`).
- `with_owner(owner_token)`: asocia la reserva con el flujo que la creo.

Flujo recomendado para POST idempotente:

1. `get_created_async(...)` para retorno rapido si ya existe resultado.
2. `with_owner(owner_token).try_reserve_async()` para obtener ownership.
3. Si no reserva: releer `get_created_async(...)`; si sigue sin resultado, responder `in progress`.
4. Ejecutar negocio solo si se obtuvo reserva.
5. `with_owner(owner_token).try_complete_async(result)` y validar su retorno antes de responder exito.

Regla de owner:

- Si el registro tiene `ownerToken`, solo el mismo owner puede completar `started -> created`.
- Si `ownerToken` es `null`, no se valida owner y el registro funciona como cache/estado simple.
- `created -> closed` no exige owner; la proteccion viene por la transicion atomica de estado.
- En produccion, idempotencia debe usar un provider compartido y atomico como Redis, DynamoDB o SQL. Memoria solo sirve para desarrollo, tests o una unica instancia.

## Estrategias sin source - Leer solo cache

```python
from Domain.Containers.CacheLibraryService.Internals.CacheStrategy import CacheStrategy

result = await cache.for_key("cfg-11-currencies") \
  .use_strategy(CacheStrategy.CACHE_ONLY) \
  .ensure_provider_available() \
  .resolve_async()
```

El ejemplo anterior es valido para datos primitivos, listas/dicts que quieras manejar como dict, o valores que el provider devuelva ya tipados.
Para modelos/adapters, usa deserializacion explicita:

```python
profile = await cache.for_key("cfg-11-profile") \
  .use_strategy(CacheStrategy.CACHE_ONLY) \
  .resolve_async(deserializer=ProfileAdapter)
```

Para flujos criticos como idempotencia, donde no se puede continuar si el provider no responde, usa `CACHE_ONLY_REQUIRED`:

```python
response = await cache.for_key(f"post-11-{message_id}") \
  .use_strategy(CacheStrategy.CACHE_ONLY_REQUIRED) \
  .resolve_async(deserializer=CreateExampleAdapter)
```

`CACHE_ONLY_REQUIRED` tambien retorna `None` si la llave no existe o no esta en `created`, pero propaga excepcion si no puede consultar el provider.

```python
profile = await cache.for_key("cfg-11-profile") \
  .use_strategy(CacheStrategy.CACHE_ONLY_THEN_CLOSE) \
  .resolve_async(deserializer=ProfileAdapter)
```

`CACHE_ONLY_THEN_CLOSE` intenta transicionar `created -> closed`.

## Estrategias con source - Cache con fallback al origen

```python
async def load_stock():
  return await inventory_query.get_stock_async(product_id)

result = await cache.for_key(f"trx-11-{product_id}") \
  .use_strategy(CacheStrategy.CACHE_THEN_SOURCE) \
  .ensure_provider_available() \
  .resolve_async(loader=load_stock, deserializer=StockAdapter)
```

## Estrategias con source - Cache con fallback y almacenamiento

```python
from datetime import timedelta

async def load_customer():
  return await customer_query.get_by_id_async(customer_id)

result = await cache.for_key(f"cfg-11-{customer_id}") \
  .use_strategy(CacheStrategy.CACHE_THEN_SOURCE_AND_STORE) \
  .with_ttl(timedelta(minutes=10), ttl_jitter=timedelta(minutes=2)) \
  .resolve_async(loader=load_customer, deserializer=CustomerAdapter)
```

Si el `loader` devuelve `None`, la libreria elimina la reserva y retorna `None`.

## Estrategias con source - Forzar origen y almacenar

```python
async def load_settings():
  return await settings_query.get_company_settings_async(company_code)

result = await cache.for_key(f"trx-11-{company_code}") \
  .use_strategy(CacheStrategy.SOURCE_AND_STORE) \
  .with_ttl(timedelta(minutes=30), ttl_jitter=timedelta(minutes=2)) \
  .resolve_async(loader=load_settings)
```

Nota: `SOURCE_AND_STORE` siempre ejecuta el `loader`; el `deserializer` solo es relevante cuando una estrategia puede retornar data ya cacheada.

## Estrategias sin source - Almacenar directamente

```python
ok = await cache.for_key(f"get-11-{message_id}") \
  .use_strategy(CacheStrategy.STORE_ONLY) \
  .with_ttl(timedelta(minutes=5), ttl_jitter=timedelta(minutes=1)) \
  .put_async(summary)
```

```python
ok = await cache.for_key(f"get-11-{message_id}") \
  .use_strategy(CacheStrategy.STORE_ONLY_OR_RESERVE) \
  .with_ttl(timedelta(minutes=5), ttl_jitter=timedelta(minutes=1)) \
  .put_async(None)
```

`STORE_ONLY_OR_RESERVE` ignora el valor y crea reserva (`started`).

## Estrategias sin source - Validar existencia

```python
exists = await cache.for_key(f"get-11-{message_id}") \
  .exists_async()
```

`exists_async` es estricto: si el provider requerido no responde o falla, propaga la excepcion para que el flujo llamador pueda bloquear la operacion.

## Deserializacion explicita

```python
result = await cache.for_key("cfg-11-profile") \
  .use_strategy(CacheStrategy.CACHE_ONLY) \
  .resolve_async(deserializer=ProfileAdapter)
```

`deserializer` puede ser:

- una funcion `callable(value) -> T`
- una clase `type[T]` (soporta `dict`, `list/tuple` o valor simple)

Cuando el provider serializa a JSON, como Redis, el dato recuperado normalmente vuelve como `dict`, `list` o valores primitivos. Por eso, si el codigo espera un modelo Pydantic, dataclass o adapter de Application, se debe pasar `deserializer` para reconstruir el tipo esperado.

## Modelo del registro

```json
{
  "id": "canonical-cache-key",
  "status": "started|created|closed",
  "cachedData": null,
  "createdAt": 1700000000,
  "expireIn": 1700000300,
  "ownerToken": null
}
```

## Reglas importantes

- `for_key(...)` recibe una sola clave exacta y deterministica.
- Solo `status = created` es cache hit funcional.
- `status = started` y `status = closed` no retornan dato valido.
- `ownerToken` es opcional; se usa para completar reservas idempotentes con ownership.
- `with_ttl(ttl, ttl_jitter)` exige `ttl > 0`.
- `ttl_jitter` debe ser `>= 0` y `< ttl / 3`.
- El timeout interno al provider es 0.5 segundos por operacion.
- Fallas del provider se tratan como fail-open (miss o escritura omitida).
- `exists_async`, `CACHE_ONLY_REQUIRED` o activar `ensure_provider_available()` son excepciones: propagan fallas porque fuerzan modo bloqueante.
- La cancelacion explicita (`asyncio.CancelledError`) si se propaga.
