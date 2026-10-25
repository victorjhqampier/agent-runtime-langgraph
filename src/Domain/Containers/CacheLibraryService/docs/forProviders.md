# CacheLibraryService - Guia tecnica para providers

## Objetivo

Este documento describe como implementar un provider para `CacheLibraryService` en Python.

Aplica a Redis, DynamoDB, MongoDB, SQL, memoria u otro storage.
El provider debe ser storage tonto: no decide estrategias, no interpreta negocio y no construye claves.

## Contrato real

Todo provider implementa `ICacheInfrastructure`:

```python
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Optional

from Domain.Containers.CacheLibraryService.Internals.CacheRecord import CacheRecord
from Domain.Containers.CacheLibraryService.Internals.CacheStatus import CacheStatus


class ICacheInfrastructure(ABC):
    @abstractmethod
    async def get_async(self, cache_id: str) -> Optional[CacheRecord[Any]]:
        pass

    @abstractmethod
    async def try_create_async(self, record: CacheRecord[Any], ttl: timedelta) -> bool:
        pass

    @abstractmethod
    async def try_update_async(self, record: CacheRecord[Any], expected_status: CacheStatus, expected_owner: Optional[str], ttl: timedelta) -> bool:
        pass

    @abstractmethod
    async def remove_async(self, cache_id: str) -> bool:
        pass

    @abstractmethod
    async def exists_async(self, cache_id: str) -> bool:
        pass
```

No hay `CancellationToken` en la firma actual.

## Modelo del registro

El storage debe persistir el registro completo:

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

Reglas:

- `id` es la clave fisica unica.
- `status` usa `started`, `created`, `closed`.
- `cachedData` puede ser `null`, objeto o arreglo.
- `createdAt` y `expireIn` son epoch seconds UTC.
- `ownerToken` es opcional y se usa para proteger reservas idempotentes.
- `ttl` y `expireIn` deben quedar alineados.

## Responsabilidad del provider

El provider solo debe:

- obtener un registro por `id`;
- crear un registro por `id` solo si no existe;
- actualizar un registro por `id` solo si el estado actual coincide con `expected_status`;
- validar owner cuando completa una reserva idempotente;
- eliminar por `id`;
- verificar existencia por `id`;
- aplicar TTL;
- fallar rapido ante problemas tecnicos.

El provider no debe:

- decidir estrategias;
- ejecutar loaders;
- componer keys;
- interpretar reglas funcionales;
- reintentar por periodos largos.

## Operaciones obligatorias

### get_async

Debe consultar por `id`.

Comportamiento recomendado:

- si no existe, retornar `None`;
- si expiro, limpiar si es barato y retornar `None`;
- si existe, retornar `CacheRecord` con su estado real.

### try_create_async

Debe crear solo si la clave no existe activa.

Comportamiento recomendado:

- `True` si creo;
- `False` si ya existia;
- no sobrescribir registros existentes;
- aplicar TTL recibido.

### try_update_async

Debe actualizar de forma condicional por `id`, `expected_status` y, cuando aplique, `expected_owner`.

Transiciones usadas por la libreria:

- `started -> created` para completar reserva;
- `created -> closed` para cierre controlado (`CACHE_ONLY_THEN_CLOSE`).

Si el estado actual no coincide con `expected_status`, retornar `False`.

Regla de owner:

- Para `started -> created`, si el registro actual tiene `ownerToken`, debe coincidir con `expected_owner`.
- Para `started -> created`, si el registro actual tiene `ownerToken = null`, no se valida owner.
- Para `created -> closed`, no se requiere owner; la garantia es que el update sea atomico y solo transicione desde `created`.

### remove_async

Elimina por `id`.

- `True` si elimino;
- `False` si no existia.

### exists_async

Verifica existencia de un registro activo por `id`.

- `True` si existe y no expiro;
- `False` en caso contrario.

## Integracion con fail-open

`CacheLibraryService` envuelve cada llamada al provider con timeout de 0.5 segundos.

Si el provider falla o excede timeout:

- la libreria usa fallback (`None` o `False`) y continua el flujo;
- `asyncio.CancelledError` si se propaga.

Excepciones donde el flujo es bloqueante (strict):

- `CACHE_ONLY_REQUIRED` en `resolve_async`;
- `exists_async`.
- cualquier operacion cuando se activa `ensure_provider_available()` en el builder.

En esos casos, si el provider falla o vence timeout, la libreria propaga excepcion.

Implicacion para providers:

- responder rapido;
- evitar retries largos;
- priorizar operaciones atomicas cortas.

## TTL

La libreria calcula:

- `expire_in` en el `CacheRecord`;
- `ttl` efectivo (con jitter opcional) enviado al provider.

El provider debe:

- rechazar o ignorar entradas con `ttl <= 0`;
- aplicar TTL nativo del motor cuando exista;
- evitar devolver registros expirados.

## Semantica de estados en lectura

El provider puede devolver cualquier estado (`started`, `created`, `closed`).
La decision de hit funcional la toma la libreria:

- solo `created` es dato usable;
- `started` y `closed` se tratan como no disponible.

## Recomendaciones de serializacion

- serializar `status` como string estable;
- mantener formato versionable;
- no acoplar modelos de Application o Presentation;
- no persistir secretos en `cachedData`.

## Ejemplo de referencia

`MemoryCacheInfrastructure` ya implementa el contrato en:

- lock async para concurrencia;
- limpieza de expirados en `get_async`;
- create condicional;
- update condicional por estado esperado.

## Checklist del provider

- Implementa `ICacheInfrastructure`.
- Usa `id` como unica clave.
- `try_create_async` no sobrescribe.
- `try_update_async` valida `id + expected_status` y owner cuando corresponde.
- Aplica TTL real.
- Falla rapido.
- No contiene reglas de negocio ni estrategias.
