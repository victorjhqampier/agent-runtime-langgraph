# Agent Runtime

Plantilla Python 3.13 para construir un Agent Runtime empresarial con arquitectura hexagonal, DI propia, LangGraph, AWS Bedrock, canales de texto/voz y pruebas de rendimiento.

## Requisitos

- Python 3.13+
- UV 0.11+
- Docker o Podman opcional
- k6 opcional para pruebas de rendimiento

## Instalación

Desde la raíz del proyecto:

```bash
uvx --from uv uv sync --dev
```

## Configuración

La aplicación carga variables desde `src/.env`. No versionar secretos, tokens ni connection strings reales.

```bash
cp src/.env.example src/.env
# editar src/.env con los valores reales del entorno
```

Ejemplo local:

```env
# LLM - AWS Bedrock
RUNTIME_LLM_PROVIDER=AWS_BEDROCK
AWS_BEDROCK_LLM_REGION=us-east-1
AWS_BEDROCK_LLM_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_BEDROCK_LLM_TEMPERATURE=0.0
AWS_BEDROCK_LLM_MAX_TOKENS=1200

# RAG - AWS Bedrock Knowledge Base
RUNTIME_RAG_PROVIDER=AWS_BEDROCK
AWS_BEDROCK_RAG_REGION=us-east-1
AWS_BEDROCK_RAG_KNOWLEDGE_BASE_ID=tu-id-de-base-de-conocimiento
AWS_BEDROCK_RAG_NUMBER_OF_RESULTS=5

# Memoria y Checkpointer - AWS Redis
RUNTIME_MEMORY_PROVIDER=AWS_REDIS
AWS_REDIS_MEMORY_HOST=tu-host-de-redis
AWS_REDIS_MEMORY_PORT=6379
AWS_REDIS_MEMORY_NAMESPACE=agent-runtime

# Guardrail - AWS Bedrock Guardrails
RUNTIME_GUARDRAIL_PROVIDER=AWS_BEDROCK
AWS_BEDROCK_GUARDRAIL_ENABLED=true
AWS_BEDROCK_GUARDRAIL_ID=tu-id-de-guardrail

# Ticketing externo - iTop
RUNTIME_TOOL_PROVIDER=ITOP
ITOP_TOOL_BASE_URL=tu-url-de-itop
ITOP_TOOL_AUTH_MODE=BEARER

# Seguridad - Runtime Security
RUNTIME_SECURITY_PII_REDACTION_ENABLED=true
```

Los valores reales deben inyectarse mediante el entorno de ejecución o un gestor de secretos. `src/.env.example` contiene la plantilla documentada.

## Arquitectura

### Dirección de dependencias

```text
Presentation -> Runtime -> Domain
                     |
                     v
                Infrastructure -> Domain
```

- **Presentation:** traduce transporte y autorización a `RuntimeRequestAdapter`. Puede usar FastAPI o el entrypoint independiente de Amazon Bedrock AgentCore.
- **Runtime:** orquesta casos de uso, workflows LangGraph, nodos, políticas y contratos de ejecución. Depende de Domain y puede registrar Infrastructure solo desde `CoreRuntimeSetting`.
- **Domain:** reglas de negocio, entidades, value objects y contratos agnósticos de tecnología. No depende de ninguna capa externa.
- **Infrastructure:** implementa contratos de Domain (Bedrock, RAG, guardrails, Redis, iTop, checkpointer y clientes externos).

### Reglas clave

- Runtime no importa FastAPI, AgentCore, LiveKit ni modelos HTTP.
- Infrastructure no importa Runtime ni Presentation.
- LangGraph thinking es obligatorio: estado explícito, nodos por responsabilidad, transiciones deterministas y checkpointer durable para reanudación.
- Los LLM son intercambiables mediante puertos de Domain (`IIncidentReasoningCommand`, `IEvidenceQuery`, `ITicketCommand`, `ITicketQuery`).
- Las acciones externas requieren autorización, timeout, idempotencia y confirmación real antes de exponerse como exitosas.

## Ejecución local

### Entrada FastAPI (opcional)

Úsala para consumidores HTTP propios o desarrollo:

```bash
uv run uvicorn Presentation.app:app \
  --app-dir src \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs/openapi`

### Entrada Amazon Bedrock AgentCore (recomendada para producción)

Funciona independientemente de FastAPI:

```bash
uv run uvicorn Presentation.AmazonAgentcore.AmazonAgentcoreRuntime:application \
  --app-dir src \
  --host 0.0.0.0 \
  --port 8080
```

- `GET /ping` -> salud del servicio
- `POST /invocations` -> atención de incidentes

Los proveedores de AWS invocan este contenedor mediante el protocolo HTTP de AgentCore Runtime.

## Arquitectura de atención de incidentes

El caso de uso inicial es `attend_incident`:

```text
entrada autenticada
    -> validación de transporte (Presentation)
    -> RuntimeRequestAdapter
    -> AttendIncidentUsecase
    -> AttendIncidentWorkflow (LangGraph)
    -> nodos (clasificación, evidencia, decisión, ticket, respuesta)
    -> RuntimeResponseAdapter
```

Estados semánticos permitidos:

- `resolved`: existe evidencia autorizada suficiente.
- `needs_clarification`: faltan datos; el workflow queda pausado con `interrupt()`.
- `escalated`: el ticket fue creado y confirmado.
- `failed`: no se pudo completar o confirmar una operación.
- `rejected`: la solicitud no está autorizada o está fuera de alcance.

El mismo Runtime puede ser invocado por FastAPI o Amazon AgentCore. Ambos transportes comparten el mismo caso de uso, workflow y contratos.

## Docker

Capa FastAPI:

```bash
docker build -t arify-agent-runtime -f Dockerfile .
docker run -p 8000:8000 arify-agent-runtime
```

Capa Amazon AgentCore Runtime:

```bash
docker build -t arify-agent-core-runtime -f Dockerfile.agentcore .
docker run -p 8080:8080 arify-agent-core-runtime
```

## Comandos de calidad

Formato:

```bash
uv run ruff format .
uv run ruff format --check .
```

Lint:

```bash
uv run ruff check .
```

Typecheck:

```bash
uv run pyrefly check
```

Compilación rápida:

```bash
uvx --from uv uv run python -m compileall -q src tests
```

## Tests

Tests unitarios:

```bash
uvx --from uv uv run python -m unittest discover -s tests/unit
```

Tests de un solo archivo:

```bash
uvx --from uv uv run python -m unittest tests.unit.test_attend_incident_workflow
uvx --from uv uv run python -m unittest tests.unit.test_amazon_agentcore_runtime
uvx --from uv uv run python -m unittest tests.unit.test_architecture_boundaries
uvx --from uv uv run python -m unittest tests.unit.test_dependency_injection
```

## Estructura del proyecto

```text
src/
├── Domain/
│   ├── Entities/
│   ├── ValueObjects/
│   ├── Enums/
│   ├── Interfaces/
│   └── Containers/
│       └── DependencyInjection/
│           └── CoreServices.py
├── Runtime/
│   ├── UseCases/
│   │   └── AttendIncident/
│   │       ├── AttendIncidentUsecase.py
│   │       ├── States/
│   │       ├── Workflows/
│   │       ├── Nodes/
│   │       ├── Prompts/
│   │       └── Schemas/
│   ├── Adapters/
│   │   ├── RuntimeRequestAdapter.py
│   │   └── RuntimeResponseAdapter.py
│   ├── Ports/
│   │   └── IRuntimeGraphPort.py
│   ├── Internals/
│   └── CoreRuntimeSetting.py
├── Presentation/
│   ├── FastApi/
│   │   └── ...
│   └── AmazonAgentcore/
│       ├── AmazonAgentcoreRuntime.py
│       └── Models/
│           └── AgentCoreInvocationRequestModel.py
└── Infrastructure/
    ├── Llms/
    ├── Rags/
    ├── Memories/
    ├── Tools/
    ├── Guardrails/
    └── Securities/
```
