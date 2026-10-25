# Domain/AGENTS.md

Guia especifica para trabajar en Domain.

Domain es el núcleo del microservicio: lenguaje ubicuo, entidades, value objects, contratos y componentes core compartidos. También puede definir capacidades agnósticas requeridas por el Agent Runtime.

## Prioridad y alcance

- Estas reglas aplican a todo lo que se edite dentro de Domain.
- Si una necesidad tecnica contradice estas reglas, la implementacion debe moverse a Infrastructure o Presentation.

## Reglas obligatorias

### Dependencias

- Domain no depende de ninguna capa del proyecto.
- Domain debe permanecer libre de detalles de HTTP, storage, drivers, SDKs y proveedores cloud.
- Domain no debe depender de LangGraph, LangChain, Bedrock, LiveKit, ASR, TTS ni APIs concretas de Help Desk.
- Lectura y escritura deben separarse en contratos: Query para lectura y Command para cambios de estado.

### Modelado de dominio

- Tipos, contratos y catalogos deben representar conceptos reales de negocio o capacidades core compartidas.
- Debe priorizarse consistencia e invariantes del dominio.
- Entidades y value objects deben validar su consistencia al crearse cuando exista regla de negocio.
- Nombres en ingles siguiendo convencion Python del repo: clases PascalCase, funciones/metodos/variables snake_case, constantes UPPER_SNAKE_CASE.
- Firmas de funciones/metodos en una sola linea, salvo limitacion tecnica inevitable.

### Estructura

- Solo se permite mantener estas carpetas principales:
- Catalogs
- Containers
- Entities
- Interfaces
- ValueObjects
- Enums
- Internals

### Interfaces

- Interfaces deben describir capacidades de dominio, no tecnologia.
- Los contratos usados por IA deben describir capacidades como recuperación autorizada, generación, ticketing o persistencia; no deben nombrarse por proveedor.
- Metodos asincronos deben ser async def.
- Si el contrato espera I/O, debe permitir cancelacion cooperativa de asyncio.
- Retornos deben ser tipos de Domain o tipos simples de dominio.

### Containers

- Containers debe contener logica core compartida sin proveedores concretos.
- Componentes en memoria deben cuidar concurrencia, cancelacion y limites de memoria.

## Reglas permitidas

- Se permite DDD pragmatica enfocada en lenguaje ubicuo.
- Se permite usar Optional solo cuando la ausencia del dato tenga significado de dominio.
- Se permite ubicar entidades internas de observabilidad en Entities/Internals.
- Se permite conservar sufijos heredados como _async cuando ya existan en contratos.
- Se permite extraer factories/metodos de dominio para proteger invariantes.

## Reglas prohibidas

### Dependencias y tecnologia

- Prohibido referenciar Application, BusinessApi, EventListener o cualquier Infrastructure.
- Prohibido agregar controllers, modelos HTTP, DTOs de proveedor, drivers, queries SQL/Mongo o SDKs cloud.
- Prohibido nombrar interfaces por tecnologia concreta (por ejemplo Mongo, Redis, SqlServer, Kafka, Sqs, HttpClient).
- Prohibido crear interfaces como `IBedrockClient`, `ILangGraphCheckpoint`, `ILiveKitService` o `IHelpDeskApi` dentro de Domain.

### Estructura

- Prohibido crear carpetas principales nuevas sin decision explicita del equipo.
- Prohibido duplicar modelos externos dentro de Entities.

### Seguridad y configuracion

- Prohibido persistir secretos, connection strings o configuracion de ambiente en Domain.

## Criterios de aceptacion antes de finalizar

- El cambio pertenece realmente a Domain.
- La direccion de dependencias permanece limpia.
- No se introducen tecnologias/proveedores concretos.
- Contratos nuevos estan separados en Query y Command cuando aplica.
- Entidades y value objects representan dominio y preservan invariantes.
- Containers no comprometen concurrencia, cancelacion ni memoria.
