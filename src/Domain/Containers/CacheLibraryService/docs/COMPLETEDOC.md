# CacheLibraryService - Documento completo

## Objetivo

Este documento describe el comportamiento real de `CacheLibraryService` segun la implementacion Python actual.

## Arquitectura

La estrategia de cache vive en:

- `CacheLibraryService`
- `CacheBuilder`

El provider (`ICacheInfrastructure`) solo realiza operaciones de storage por clave.

## Componentes

### `CacheLibraryService`

- Constructor: `CacheLibraryService(provider: ICacheInfrastructure)`
- Metodo: `for_key(key: str) -> CacheBuilder`

Valida que `provider` no sea `None` y que `key` no sea vacio.

### `CacheBuilder`

Configuracion interna:

- estrategia default: `CacheStrategy.CACHE_THEN_SOURCE_AND_STORE`
- TTL default: 5 minutos
- jitter default: 0
- timeout de provider: 0.5 segundos

API publica:

- `use_strategy(strategy: CacheStrategy) -> CacheBuilder`
- `with_owner(owner_token: str) -> CacheBuilder`
- `with_ttl(ttl: timedelta, ttl_jitter: timedelta = timedelta(0)) -> CacheBuilder`
- `ensure_provider_available(required: bool = True) -> CacheBuilder`
- `resolve_async(loader=None, deserializer=None) -> Optional[T]`
- `put_async(value: Any = None) -> bool`
- `remove_async() -> bool`
- `exists_async() -> bool`

## Estrategias soportadas

| Estrategia | Metodo valido | Comportamiento |
|---|---|---|
| `CACHE_ONLY` | `resolve_async` | Lee solo `created`. |
| `CACHE_ONLY_REQUIRED` | `resolve_async` | Lee solo `created` y propaga fallas del provider. |
| `CACHE_ONLY_THEN_CLOSE` | `resolve_async` | Lee `created` y trata de cerrar a `closed`. |
| `CACHE_THEN_SOURCE` | `resolve_async` | Intenta cache; si no hay hit, ejecuta loader. |
| `CACHE_THEN_SOURCE_AND_STORE` | `resolve_async` | Intenta cache; si no hay hit, reserva/carga/guarda. |
| `SOURCE_AND_STORE` | `resolve_async` | Ejecuta loader y guarda si hay valor. |
| `STORE_ONLY` | `put_async` | Guarda valor como `created`. |
| `STORE_ONLY_OR_RESERVE` | `put_async` | Crea reserva `started`. |

Uso invalido:

- `resolve_async` con estrategia de `put` lanza `ValueError`.
- `put_async` con estrategia de `resolve` lanza `ValueError`.

## Estados y transiciones

Estados:

- `started`
- `created`
- `closed`

Reglas de lectura:

- solo `created` es hit funcional;
- `started` y `closed` retornan `None`.

Transiciones usadas por la implementacion:

- `started -> created` al completar reserva en `store_created`;
- `created -> closed` en `CACHE_ONLY_THEN_CLOSE`.

Owner:

- `ownerToken` es opcional en el registro.
- Si un registro `started` tiene `ownerToken`, solo el mismo owner puede completar `started -> created`.
- Si `ownerToken` es `null`, no se valida owner.
- `created -> closed` no exige owner; depende de la transicion atomica desde `created`.

## TTL y jitter

Reglas de `with_ttl`:

- `ttl` debe ser `> 0`;
- `ttl_jitter` no puede ser negativo;
- si hay jitter, debe ser `< ttl / 3`.

TTL efectivo:

- con jitter, se calcula variacion aleatoria uniforme `[-jitter, +jitter]`;
- TTL minimo aplicado: 1 ms.

`created_at` y `expire_in` se persisten como epoch seconds UTC.

## Comportamiento de fail-open y lecturas requeridas

Todas las operaciones contra provider se ejecutan con timeout de 0.5 segundos.

Si falla una llamada al provider (error o timeout):

- `get` devuelve fallback `None`;
- `create/update/remove` devuelven fallback `False`.

Excepciones:

- `CACHE_ONLY_REQUIRED` propaga fallas de `get`;
- `exists_async` propaga fallas de `exists`;
- `ensure_provider_available()` activa modo estricto para operaciones del builder;
- `asyncio.CancelledError` si se propaga.

## Semantica por flujo

### `CACHE_ONLY`

- lee registro;
- retorna valor deserializado solo si estado es `created`.

### `CACHE_ONLY_REQUIRED`

- lee registro usando provider requerido;
- retorna valor deserializado solo si estado es `created`;
- retorna `None` si el provider responde que no hay registro, o si el estado no es `created`;
- propaga excepcion si el provider falla o no responde dentro del timeout interno.

### `CACHE_ONLY_THEN_CLOSE`

- lee registro `created`;
- intenta update condicional a `closed` esperando `created`;
- retorna dato solo si el cierre se logro.

### `CACHE_THEN_SOURCE`

- intenta cache;
- si no hay hit, ejecuta `loader`;
- no guarda resultado.

### `CACHE_THEN_SOURCE_AND_STORE`

Flujo:

1. Si existe `created`, retorna cache.
2. Si existe `started` o `closed`, retorna `None`.
3. Si no existe, intenta reservar (`started`).
4. Si no reserva, vuelve a leer para detectar concurrencia.
5. Si luego de concurrencia hay `created`, retorna cache.
6. Si hay `started` o `closed`, retorna `None`.
7. Si logra ejecutar loader:
   - si `loader` devuelve `None`, elimina clave y retorna `None`;
   - si devuelve valor, guarda `created` y retorna valor.
8. Si loader lanza excepcion, elimina clave y relanza excepcion.

### `SOURCE_AND_STORE`

- ejecuta loader;
- si valor es `None`, retorna `None`;
- si hay valor, guarda `created` y retorna valor.

### `STORE_ONLY`

- intenta crear `created`;
- si ya existe `started`, intenta completar a `created`;
- en cualquier otro estado, retorna `False`.

### `STORE_ONLY_OR_RESERVE`

- crea registro `started`;
- no usa el valor recibido en `put_async`.

## Deserializacion

`resolve_async` acepta `deserializer` opcional:

- `callable(value) -> T`
- `type[T]`

Si se pasa tipo:

- si el valor ya es instancia del tipo, lo retorna;
- si el valor es `dict`, hace `type(**value)`;
- si es `list/tuple`, hace `type(*value)`;
- en otro caso, hace `type(value)`.

## Contrato de provider

`ICacheInfrastructure` define:

- `get_async(cache_id)`
- `try_create_async(record, ttl)`
- `try_update_async(record, expected_status, expected_owner, ttl)`
- `remove_async(cache_id)`
- `exists_async(cache_id)`

Implementacion de referencia:

- `MemoryCacheInfrastructure` con lock async y limpieza de expirados.

## Ejemplo minimo de uso

```python
from datetime import timedelta

from Domain.Containers.CacheLibraryService.CacheLibraryService import CacheLibraryService
from Domain.Containers.CacheLibraryService.Internals.CacheStrategy import CacheStrategy
from Domain.Containers.CacheLibraryService.Internals.MemoryCacheInfrastructure import MemoryCacheInfrastructure

provider = MemoryCacheInfrastructure()
cache = CacheLibraryService(provider)


async def load_customer():
    return {"customer_id": "C-001", "name": "Ada"}


result = await cache.for_key("cfg-11-customer-C-001") \
    .use_strategy(CacheStrategy.CACHE_THEN_SOURCE_AND_STORE) \
    .with_ttl(timedelta(minutes=10), ttl_jitter=timedelta(minutes=2)) \
    .resolve_async(loader=load_customer)
```
