"""Workflow LangGraph del caso de uso AttendIncident.

AttendIncidentWorkflow construye el grafo de estado con nodos, aristas y transiciones
condicionales. Implementa IRuntimeGraphPort y encapsula el motor LangGraph tras los
puertos de Domain.

Reglas para un junior:
- El workflow define el orden y las condiciones de ejecución; los nodos solo hacen una operación.
- Las rutas críticas son determinísticas: un LLM no define ni puede omitir políticas ni validaciones.
- Usar checkpointer duradero con thread_id estable para reanudar execuciones pausadas (interrupt).
- No importar Infrastructure directamente. Solo puertos de Domain.
- maximum_clarification_attempts es una política explícita para evitar conversaciones indefinidas.
"""

from Runtime.UseCases.AttendIncident.Workflows.AttendIncidentWorkflow import AttendIncidentWorkflow
