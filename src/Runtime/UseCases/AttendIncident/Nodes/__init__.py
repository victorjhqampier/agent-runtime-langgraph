"""Nodos LangGraph del caso de uso AttendIncident.

IncidentWorkflowNodes agrupa todas las operaciones del workflow como nodos de una sola
responsabilidad. Cada nodo transforma IncidentState y devuelve un diccionario de actualizaciones
que LangGraph aplica al estado.

Reglas para un junior:
- Un nodo = una responsabilidad de negocio (no una operación del framework ni del proveedor).
- Los nodos solo conocen puertos de Domain (IIncidentReasoningCommand, IEvidenceQuery, ITicketCommand, ITicketQuery).
- Nunca importar clientes AWS, LiveKit ni modelos HTTP.
- No guardar secretos, credenciales ni prompts renderizados en el estado.
- Las acciones externas (crear ticket) se separan de los nodos LLM y requieren confirmación real.
- interrupt() solo se usa dentro de nodos de pausa y requiere checkpointer duradero + thread_id estable.
"""
