# Inyeccion OpenTelemetry Para Python 3.13 FastAPI

Esta plantilla inyecta OpenTelemetry en una aplicacion Python 3.13 FastAPI sin cambiar codigo fuente ni el Dockerfile de produccion.

## Artefacto Requerido

Por defecto no se requiere ningun artefacto manual.

La plantilla de Compose instala los paquetes OpenTelemetry al iniciar el contenedor:

```bash
python -m pip install --no-cache-dir opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
opentelemetry-instrument uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Requisitos

La imagen de la aplicacion debe tener:

- Runtime compatible con Python 3.13.
- `pip` disponible.
- Acceso a internet para instalar paquetes.
- Permisos de escritura para instalar paquetes.
- Un entrypoint ASGI que coincida con `app.main:app`, o ajustar el `command` del Compose.
- Un entrypoint que permita ejecutar el override de `command` definido en Compose.

## Como Se Inyecta

La plantilla de Compose instala OpenTelemetry, ejecuta bootstrap discovery y arranca FastAPI mediante `opentelemetry-instrument`:

```yaml
command:
  - sh
  - -c
  - >
    python -m pip install --no-cache-dir
    opentelemetry-distro
    opentelemetry-exporter-otlp &&
    opentelemetry-bootstrap -a install &&
    opentelemetry-instrument uvicorn app.main:app --host 0.0.0.0 --port 8080
```

La telemetria se envia al Collector con:

```yaml
OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318
OTEL_EXPORTER_OTLP_PROTOCOL: http/protobuf
OTEL_TRACES_EXPORTER: otlp
```

No apuntes la app directamente a `jaeger`.

## Limites

La plantilla mantiene el limite de hardware para ambientes bajos:

```yaml
cpus: "0.5"
mem_limit: 700m
memswap_limit: 700m
```

## Validacion

Valida el archivo Compose:

```bash
docker compose -f app-tracer-autoinstrument/python-313-fastapi/docker-compose.yaml config
podman compose -f app-tracer-autoinstrument/python-313-fastapi/docker-compose.yaml config
```

Verifica que el wrapper y los paquetes existan despues de que el contenedor arranque:

```bash
docker compose exec python-313-fastapi-app which opentelemetry-instrument
docker compose exec python-313-fastapi-app python -m pip list | grep opentelemetry
```

La app esta disponible en `http://localhost:8000` (el contenedor escucha en 8080, el host expone 8000).

Genera trafico contra la app y luego revisa logs del Collector y Jaeger:

```bash
docker compose logs -f otel-collector
```

Abre `http://localhost:16686` y busca `python-313-fastapi-app` o el `OTEL_SERVICE_NAME` configurado.

## Notas

- Instalar paquetes al inicio es practico para ambientes bajos, pero es mas lento y depende de acceso a internet.
- Para ambientes controlados, usa una imagen solo para lower environments o monta un virtualenv Python 3.13 preconstruido.
- Cambia `app.main:app` si la app FastAPI real usa otra ruta de modulo.
