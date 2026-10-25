# Attend Incident: Flujos conversacionales

Este documento define el comportamiento conversacional esperado del caso de uso `AttendIncident` antes de diseñar nodos, prompts o integraciones. Es la especificación funcional de alto nivel para la implementación basada en LangGraph thinking.

## Alcance y unidad de workflow

`AttendIncident` cubre exclusivamente mesa de ayuda e incidentes de sistemas informáticos: aplicaciones, accesos, VPN, infraestructura y servicios tecnológicos.

Las diez simulaciones de este documento son rutas conversacionales de **un único workflow `AttendIncident`**. No son workflows independientes: comparten estado, `thread_id`, contexto conversacional, políticas de mesa de ayuda y contrato de respuesta.

Procesos de otros dominios, como tasas, scores, excepciones de negocio, aprobaciones u operaciones comerciales, deben pertenecer a otros casos de uso y workflows. No se incorporan como rutas de `AttendIncident`.

## Flujo unificado

```text
Usuario plantea un incidente
        |
        v
Agente analiza intención y evidencia autorizada
        |
        +-- Evidencia suficiente ----------------------> responde y finaliza
        |
        +-- Información insuficiente ------------------> solicita aclaración
        |                                                   |
        |                                                   +-- incidente documentado --> responde y finaliza
        |                                                   |
        |                                                   +-- no documentado -------> solicita confirmación de ticket
        |
        +-- Sin evidencia desde el inicio -------------> solicita confirmación de ticket
                                                            |
                                                            +-- confirmación positiva --> crea y confirma ticket
                                                            |
                                                            +-- confirmación negativa --> no crea ticket y finaliza
```

Los casos dos, tres y cuatro son ramas del mismo flujo conversacional. El mismo `thread_id` debe conservarse mientras el agente solicita información o espera confirmación.

## Interacción entre workflow, nodos e Infrastructure

```text
RuntimeRequestAdapter
        |
        v
AttendIncidentUsecase
        |
        v
IRuntimeGraphPort
        |
        v
AttendIncidentWorkflow (LangGraph)
        |
        +-- IncidentWorkflowNodes
        |       |
        |       +-- IIncidentReasoningCommand --> adaptador LLM de Infrastructure
        |       +-- IEvidenceQuery -----------> adaptador RAG de Infrastructure
        |       +-- ITicketCommand -----------> adaptador de ticketing de Infrastructure
        |
        +-- checkpointer durable de Redis
        |
        v
IncidentState
        |
        v
RuntimeResponseAdapter
```

El workflow es el único responsable de las transiciones. Los nodos realizan una sola operación sobre `IncidentState` y sólo conocen puertos neutrales. Infrastructure implementa esos puertos; por ello se puede sustituir el proveedor LLM, RAG, ticketing o memoria sin modificar el workflow ni los nodos.

## Caso 1: Incidente recurrente y documentado

### Objetivo

Resolver en el primer turno un incidente conocido, con evidencia autorizada y suficiente.

### Simulación

```text
Usuario:
  Mi VPN no conecta desde esta mañana.

Agente:
  Identifiqué un incidente conocido relacionado con la VPN.
  Para resolverlo, reinicia el cliente VPN y vuelve a autenticarte.
  Si el problema continúa, indícame el mensaje de error exacto.
```

### Resultado esperado

```text
resolution_status = resolved
ticket = none
interrupt = none
```

No se crea ticket ni se solicita una nueva interacción cuando la evidencia permite dar una respuesta confiable.

## Caso 2: Solicitud ambigua que se resuelve conversando

### Objetivo

Solicitar sólo la información necesaria para identificar un incidente documentado y resolverlo dentro de la misma conversación.

### Simulación

```text
Usuario:
  No funciona.

Agente:
  ¿Qué servicio presenta el problema?

Usuario:
  La VPN.

Agente:
  ¿El problema ocurre al iniciar sesión o después de conectarte?

Usuario:
  Después de conectarme. Me desconecta a los pocos segundos.

Agente:
  Identifiqué un incidente documentado relacionado con desconexiones de VPN.
  Aplica esta solución: ...
```

### Resultado esperado

```text
needs_clarification
    -> needs_clarification
    -> resolved
```

Cada pregunta debe reducir la ambigüedad. La conversación debe conservar el contexto previamente obtenido y no volver a preguntar datos ya proporcionados.

## Caso 3: Incidente no documentado después de aclaraciones

### Objetivo

Determinar, después de reunir información suficiente, que no existe un procedimiento documentado y solicitar autorización explícita antes de crear un ticket.

### Simulación

```text
Usuario:
  Tengo problemas con el sistema.

Agente:
  ¿Qué sistema presenta el problema y qué comportamiento observas?

Usuario:
  Es una aplicación interna. Se cierra, pero no sé por qué.

Agente:
  Con la información proporcionada no encuentro un procedimiento documentado.
  ¿Deseas que cree un ticket para que el equipo lo revise?

Usuario:
  Sí, créalo.

Agente:
  El ticket INC-123 fue creado correctamente.
  El equipo revisará el incidente.
```

### Resultado esperado

```text
needs_clarification
    -> needs_clarification
    -> needs_clarification (confirmación de ticket)
    -> escalated
```

El ticket sólo puede crearse después de una confirmación explícita y de una respuesta confirmada por el sistema externo.

## Caso 4: Incidente no encontrado directamente

### Objetivo

Solicitar confirmación para escalar cuando la búsqueda inicial no encuentra evidencia suficiente y el mensaje ya aporta información identificable.

### Simulación

```text
Usuario:
  El sistema muestra el error XJ-9482.

Agente:
  No encontré documentación suficiente para el error XJ-9482.
  ¿Deseas que cree un ticket para investigarlo?

Usuario:
  Sí.

Agente:
  El ticket INC-456 fue creado correctamente.
```

### Resultado esperado

```text
needs_clarification (confirmación de ticket)
    -> escalated
```

La diferencia frente al caso tres es que aquí no se requieren aclaraciones previas: el mensaje permite ejecutar la búsqueda inicial, pero esta no aporta evidencia suficiente.

## Caso 5: Usuario rechaza crear el ticket

### Objetivo

Finalizar la conversación sin acción externa cuando el usuario no autoriza el escalamiento.

### Simulación

```text
Agente:
  No encontré documentación suficiente para resolver el incidente.
  ¿Deseas que cree un ticket para investigarlo?

Usuario:
  No, por ahora no.

Agente:
  Entendido. No crearé ningún ticket. Si deseas retomarlo más adelante,
  podrás indicarme que continuemos con este incidente.
```

### Resultado esperado

```text
needs_clarification (confirmación de ticket)
    -> resolved
ticket = none
```

La decisión negativa debe quedar registrada en el estado de la conversación para no intentar crear el ticket en reintentos posteriores del mismo turno.

## Caso 6: No se puede confirmar la creación del ticket

### Objetivo

Comunicar un fallo técnico sin afirmar que el ticket fue creado.

### Simulación

```text
Agente:
  No encontré un procedimiento documentado. ¿Deseas que cree un ticket?

Usuario:
  Sí, créalo.

Agente:
  No pude confirmar la creación del ticket debido a un problema temporal.
  No afirmaré que fue registrado. Puedes intentarlo nuevamente más tarde.
```

### Resultado esperado

```text
confirmación positiva
    -> intento de creación
    -> failed
ticket = none o estado no confirmado
```

La respuesta sólo puede confirmar la creación después de recibir una confirmación real del sistema externo.

## Caso 7: La solución documentada no resolvió el incidente

### Objetivo

Escalar un incidente cuando el usuario informa que la solución documentada ya fue aplicada sin éxito.

### Simulación

```text
Agente:
  Aplica esta solución documentada: reinicia el cliente VPN y vuelve a autenticarte.

Usuario:
  Ya lo hice y el problema continúa.

Agente:
  La solución documentada no resolvió el incidente.
  ¿Deseas que cree un ticket para que el equipo lo revise?
```

### Resultado esperado

```text
resolved inicial
    -> needs_clarification (confirmación de ticket)
```

El agente debe conservar que la solución fue intentada para no sugerirla nuevamente en la misma conversación.

## Caso 8: Se alcanza el límite de aclaraciones

### Objetivo

Evitar conversaciones indefinidas cuando las respuestas no permiten identificar ni resolver el incidente.

### Simulación

```text
Usuario:
  No funciona.

Agente:
  ¿Qué servicio presenta el problema?

Usuario:
  No sé.

Agente:
  ¿Qué mensaje de error aparece o desde cuándo ocurre?

Usuario:
  No sé.

Agente:
  No tengo información suficiente para identificar el incidente.
  ¿Deseas que cree un ticket para que el equipo lo investigue?
```

### Resultado esperado

```text
needs_clarification
    -> needs_clarification
    -> needs_clarification (confirmación de ticket)
```

El máximo de preguntas será una política explícita del workflow; al alcanzarlo, el agente debe ofrecer escalamiento y no continuar preguntando indefinidamente.

## Caso 9: Reanudación de una confirmación pendiente

### Objetivo

Continuar una conversación interrumpida sin repetir la búsqueda ni perder el contexto previo.

### Simulación

```text
Agente:
  No encontré documentación suficiente para el error XJ-9482.
  ¿Deseas que cree un ticket para investigarlo?

Usuario:
  Sí, créalo.

Agente:
  El ticket INC-456 fue creado correctamente.
```

### Resultado esperado

```text
interrupt de confirmación
    -> reanudación con el mismo thread_id
    -> escalated
```

La reanudación debe usar el estado durable asociado al mismo `thread_id`; no debe volver a ejecutar ni preguntar los pasos ya completados.

## Caso 10: Reintento o mensaje duplicado

### Objetivo

Evitar tickets duplicados cuando el transporte reintenta un mensaje o entrega el mismo turno más de una vez.

### Simulación

```text
Usuario:
  Sí, créalo.

Sistema:
  Reintenta el mismo mensaje por una demora de red.

Agente:
  El ticket INC-456 ya fue creado para este incidente.
```

### Resultado esperado

```text
misma idempotency_key
    -> reutilizar resultado confirmado
    -> no repetir la creación externa
    -> escalated
```

La idempotencia debe proteger la acción externa incluso si llegan solicitudes concurrentes o reintentos del mismo turno.

## Reglas transversales

- La evidencia recuperada es información no confiable hasta que el Runtime valide que es autorizada y suficiente para responder.
- El agente no debe afirmar que un ticket fue creado sin confirmación real del sistema externo.
- La creación de tickets debe usar una clave de idempotencia para evitar duplicados ante reintentos del transporte.
- Las preguntas de aclaración deben ser concretas, necesarias y limitadas; el agente no debe prolongar la conversación sin mejorar la decisión.
- Una confirmación de ticket debe indicar claramente la acción que se realizará.
- La respuesta de una interrupción debe incluir el `thread_id` necesario para continuar la conversación.
- Una conversación pausada puede finalizar sin ticket si el usuario rechaza la creación o cancela la solicitud.

## Decisiones pendientes antes de implementar

- Número máximo de preguntas de aclaración antes de ofrecer escalamiento.
- Datos mínimos requeridos para crear un ticket.
- Criterio de evidencia suficiente y manejo de evidencia contradictoria.
- Comportamiento cuando el usuario cambia de incidente durante una conversación pausada.
- Tiempo de retención del estado conversacional y de las interrupciones.
