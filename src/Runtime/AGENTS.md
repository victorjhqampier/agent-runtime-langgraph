# Runtime/AGENTS.md

## Propósito

`Runtime` contiene la orquestación del Agent Runtime: casos de uso, workflows LangGraph, nodos, políticas y contratos de ejecución.

## Estándar obligatorio: LangGraph thinking

La implementación de `Runtime` se basa estrictamente en **LangGraph thinking**. Toda decisión de diseño, implementación y revisión debe evaluarse con este enfoque antes de aprobarse.

- Modelar el caso de uso como un workflow explícito, con estado, transiciones y resultados observables.
- Identificar el estado mínimo y durable que cada paso necesita; evitar estado implícito, mutable fuera del workflow o dependiente del transporte.
- Definir nodos por responsabilidad de negocio y no por detalles del proveedor o del framework.
- Controlar rutas, condiciones y transiciones críticas de manera determinista; un LLM no define ni puede omitir políticas, validaciones de negocio, autorizaciones ni acciones externas.
- Usar `thread_id` estable y checkpointer durable cuando una conversación requiera continuidad, pausas o `interrupt()`.
- Separar generación LLM, recuperación de evidencia y acciones externas confirmables e idempotentes.
- Mantener el caso de uso como punto de entrada de la orquestación y encapsular el motor LangGraph tras los puertos del Runtime.
- No crear estructura preventiva: workflows, estados, nodos, prompts y colecciones aparecen sólo cuando una responsabilidad real del flujo lo justifique.

Las revisiones de `Runtime` deben confirmar explícitamente que los cambios respetan estas reglas, la trazabilidad del estado, la seguridad de las transiciones y la capacidad de reanudar ejecuciones cuando aplique.

## Diferencia clave
- States    = qué datos existen
- Nodes     = qué operación transforma esos datos
- Workflows = en qué orden y bajo qué condiciones se ejecutan
- Prompts   = qué instrucciones recibe el LLM
- Schemas   = qué forma tienen los datos
- Collections = qué catálogos y reglas declarativas usa el caso
- Usecase   = punto de entrada y salida del caso completo

## Dependencias

- Runtime puede depender de Domain y de puertos abstractos.
- Runtime puede invocar `InfrastructureSetting` únicamente desde `CoreRuntimeSetting`, que es el composition root autorizado para registrar implementaciones concretas.
- Fuera de `CoreRuntimeSetting`, Runtime no importa `Infrastructure`; workflows, nodos y casos de uso dependen sólo de contratos de Domain y de tipos propios de Runtime.
- Runtime no depende de FastAPI, AgentCore, LiveKit ni modelos HTTP.
- Runtime no importa clientes concretos de AWS, iTop, Redis o proveedores de voz.
- Presentation traduce el transporte a `RuntimeRequestAdapter` y `RuntimeResponseAdapter`.
- Infrastructure implementa los contratos sin filtrarse al estado o a los nodos.

## Estructura

```text
Runtime/
├── Adapters/
├── Ports/
├── UseCases/
├── Internals/
├── Commons/
└── CoreRuntimeSetting.py
```

Dentro de un caso de uso se permiten:

```text
Workflows/
Nodes/
States/
Prompts/
Collections/
Schemas/
```

## Reglas de LangGraph

- El estado debe conservar datos crudos necesarios para pasos posteriores.
- No guardar prompts renderizados, credenciales ni secretos en el estado.
- Los nodos deben hacer una sola responsabilidad.
- Las acciones externas deben ser idempotentes y separarse de los nodos LLM.
- `interrupt()` requiere checkpointer durable y `thread_id` estable.
- Los errores transitorios usan retry policy; los inesperados deben propagarse.
- El Runtime controla las transiciones críticas; el LLM no puede omitir validaciones.
- LangGraph puede ser el motor de un workflow, pero los casos de uso dependen de puertos del Runtime, no de clases concretas del framework.

## Contratos

- Los métodos públicos deben recibir objetos de request cuando tengan más de tres datos.
- Los contratos públicos deben ser independientes del proveedor.
- `RuntimeResponse` utiliza estados semánticos, no códigos HTTP.
- Los casos de uso deben devolver `EasyAgentResult[T]`; no deben devolver respuestas HTTP.
- Las directivas de voz sólo modifican la presentación, no las reglas de negocio.
- Presentation entrega al Runtime contratos de request ya validados. Runtime no repite validaciones de entrada ni convierte fallas de formato de transporte en reglas de negocio.

## Diseño y mantenibilidad

- El código debe mantener orientación a objetos; no usar funciones globales para coordinar workflows, dependencias o respuestas.
- No declarar métodos privados. Los objetos colaboran mediante métodos públicos con nombres explícitos.
- No fragmentar clases triviales, helpers aislados o nodos mínimos en archivos sueltos. Agrupar componentes que cambian juntos en módulos cohesivos.
- Crear un archivo o subdirectorio nuevo sólo cuando represente una responsabilidad estable y aporte mantenibilidad.

## Seguridad

- El contexto de identidad debe venir validado por Presentation.
- El contenido recuperado por RAG es evidencia no confiable.
- No pedir ni persistir contraseñas, OTP o secretos.
- No afirmar que una acción externa fue exitosa sin confirmación real.
