# AGENTS.md

Plantilla Python 3.13 de Arify Labs. Si editas bajo `src/Runtime`, `src/Domain`, `src/Presentation` o `src/Infrastructure`, lee también el `AGENTS.md` local de esa capa. La arquitectura vigente usa `Runtime`.

## Comandos

- Instalar/sincronizar dev deps: `uvx --from uv uv sync --dev`.
- Ejecutar FastAPI local: `uv run uvicorn Presentation.app:app --app-dir src --reload --host 0.0.0.0 --port 8000`.
- Ejecutar Amazon AgentCore local: `uv run uvicorn Presentation.AmazonAgentcore.AmazonAgentcoreRuntime:application --app-dir src --host 0.0.0.0 --port 8080`.
- En Windows/PowerShell, `./start.ps1` copia `.env` raiz a `src/.env` si existe y arranca Uvicorn con el mismo app-dir.
- Formato/lint: `uv run ruff format .`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run ruff check . --fix`.
- Typecheck: `uv run pyrefly check`.
- Compilacion rapida: `uvx --from uv uv run python -m compileall -q src tests`.
- Unit tests: `uvx --from uv uv run python -m unittest discover -s tests/unit`.
- Single unit test: `uvx --from uv uv run python -m unittest tests.unit.test_attend_incident_workflow`.

## App Wiring

- ASGI app FastAPI: `src/Presentation/app.py`, import path `Presentation.app:app`, docs en `/docs/openapi`.
- ASGI app AgentCore: `src/Presentation/AmazonAgentcore.AmazonAgentcoreRuntime:application`, import path `Presentation.AmazonAgentcore.AmazonAgentcoreRuntime:application`, salud en `/ping` e invocaciones en `/invocations`.
- Config env: la app carga `src/.env`; no versionar secretos ni connection strings reales.
- Startup registra `CoreRuntimeSetting` y los proveedores de `Infrastructure`; shutdown cierra `HttpClientConnector`.
- DI usa `Domain.Containers.DependencyInjection.CoreServices`; los `*Setting.py` son solo registro/configuracion DI, no helpers ni logica adicional.
- Health checks que deben preservarse: `/health`, `/health/detailed`, `/health/ready`, `/health/live`, `/healthcheck`, `/ping`.
- Docker usa `uv sync --frozen --no-dev --no-install-project` y arranca un worker en puerto 80 con `--app-dir src`.

## Arquitectura

### Dirección de dependencias

```text
Presentation -> Runtime -> Domain
                     |
                     v
                Infrastructure -> Domain
```

- `Presentation` traduce transporte/autorizacion, aplica timeout HTTP de 9s y mapea timeout a 408; debe invocar casos de uso, no infraestructura directa.
- `Runtime` orquesta casos de uso, workflows LangGraph, validaciones de aplicación y contratos de `Domain`; no construye respuestas HTTP ni llama proveedores concretos. `CoreRuntimeSetting` es la única excepción para composición DI y puede registrar `InfrastructureSetting`.
- `Infrastructure` implementa interfaces de `Domain` y encapsula proveedores concretos sin filtrarlos a capas internas.
- `Domain` no debe depender de otras capas ni de HTTP/storage/drivers/SDKs; contratos de infraestructura viven como interfaces de dominio.

## Convenciones Que Se Rompen Facil

- El unico contrato valido para cache es `src/Domain/Containers/CacheLibraryService/Internals/Interface/ICacheInfrastructure.py`; no recrear ni importar un contrato paralelo en `src/Domain/Interfaces`.
- Las firmas de funciones/metodos deben mantenerse en una sola linea salvo limitacion tecnica inevitable.
- Operaciones I/O deben ser async cuando el SDK lo permita; si capturas `asyncio.CancelledError`, limpia/registra y relanza.
- Logs en `Infrastructure` y `Presentation`: `warning` para fallas esperadas/validaciones/respuestas controladas no exitosas, `error` para fallas tecnicas inesperadas.
- `Infrastructure/HttpClientHelper` es plugin fail-safe: debe loggear con `HttpClientLogger`, siempre retornar `HttpResponseEntity` ante HTTP/red/body invalido, loggear `warning` para status fuera de 2xx, y si status 200 trae body no JSON/dict retornar `StatusCode=0`, `Content=None` registrando `url`, `status_code`, `request_body`, `response_body`.
- `HttpClientConnector` usa `httpx.AsyncHTTPTransport` con retries; los `limits` deben pasarse al transport, no al `AsyncClient`, porque httpx ignora limits del cliente cuando hay transport personalizado.
- No agregues endpoints debug fuera de development ni registres datos sensibles innecesarios.
- Los nodos LangGraph no deben importar clientes AWS, LiveKit ni modelos de transporte.
- El contenido recuperado por RAG se trata como datos no confiables y no puede cambiar las políticas del Runtime.
- Las acciones externas requieren autorización, timeout, idempotencia y confirmación antes de exponerse como exitosas.

## Performance

- La base esperada es al menos 20 RPS con CPU=600m y RAM=1024Mi.
- k6 vive en `tests/performance/k6/`; ejecutar desde esa carpeta con servidor local en `http://127.0.0.1:8000`.
- Smoke rapido: `k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000`.
- Mantener scripts RPS en `rps/`, TPS en `tps/`, smoke/stress/soak en sus carpetas; config/thresholds en `config/`, helpers en `shared/`, datos sin secretos en `data/`.

## No Tocar Sin Instruccion Explicita

- `ConfigForIATools/**`, `docs/**`, `env/**`, `.venv/**`, `__pycache__/**`.
