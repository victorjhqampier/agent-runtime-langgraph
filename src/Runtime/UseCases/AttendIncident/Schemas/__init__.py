"""Contratos públicos (schemas Pydantic) del caso de uso AttendIncident.

Define las formas de datos que viajan entre Runtime y Presentation, y dentro del workflow:
- UserContext: contexto de identidad del usuario (validado por Presentation).
- RuntimeResponse: respuesta final con estados semánticos, citas, ticket, interrupción y directivas de voz.
- ResumeInput: entrada para reanudar un workflow interrumpido.

Reglas para un junior:
- Estos son contratos de Domain/Runtime, no modelos HTTP de Presentation.
- No nombrar proveedores concretos ni tecnologías de infraestructura.
- Usar Literal para estados semánticos cerrados (resolved, needs_clarification, escalated, failed, rejected).
"""
