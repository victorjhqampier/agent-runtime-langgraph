"""Definición del estado LangGraph para el caso de uso AttendIncident.

IncidentState es un TypedDict que representa el estado mutable del workflow a lo largo
de sus nodos. LangGraph fusiona las actualizaciones de cada nodo en este estado.

Reglas para un junior:
- El estado debe conservar solo datos crudos necesarios para pasos posteriores.
- No guardar prompts renderizados, credenciales ni secretos en el estado.
- Usar operator.add para campos que se acumulan (ej. conversation_history).
- Cada campo tiene un tipo definido; total=False permite campos opciales según la etapa.
"""

from Runtime.UseCases.AttendIncident.States.IncidentState import IncidentState
