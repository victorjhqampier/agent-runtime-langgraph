"""Caso de uso AttendIncident: atención de incidentes de TI y mesa de ayuda.

Este paquete contiene la orquestación completa del caso de uso `attend_incident` basado en LangGraph thinking.
Responsabilidades del paquete:
- Recibir una solicitud validada por Presentation (RuntimeRequestAdapter).
- Ejecutar el workflow LangGraph que clasifica, busca evidencia, aclara, crea tickets o responde al usuario.
- Devolver un EasyAgentResult con RuntimeResponseAdapter (estados semánticos, no códigos HTTP).

Reglas clave para cualquier cambio aquí:
- Runtime NO importa ni registra Infrastructure. Solo depende de Domain y de puertos abstractos.
- Los nodos hacen una sola responsabilidad y no conocen clientes AWS, LiveKit ni modelos HTTP.
- El estado (IncidentState) no guarda secretos, credenciales ni prompts renderizados.
- Las acciones externas (tickets) requieren confirmación real antes de exponerse como exitosas.
"""
