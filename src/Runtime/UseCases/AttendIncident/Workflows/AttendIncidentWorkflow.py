from typing import Any, Literal, cast
from Domain.Containers.DependencyInjection.CoreServices import CoreServices as Services
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.Config.ContextConfig import ContextConfig
from Runtime.UseCases.AttendIncident.Nodes.IncidentNodes import IncidentNodes
from Runtime.UseCases.AttendIncident.States.IncidentState import IncidentState

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Main Workflow for the `attend_incident` use case.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 08/11/2026
# *
# **********************************************************************************************************

class AttendIncidentWorkflow(IRuntimeGraphPort):
    """Workflow LangGraph del caso de uso `attend_incident`.

    Construye y compila el `StateGraph` con nodos, aristas y transiciones condicionales.
    Implementa `IRuntimeGraphPort` y encapsula el motor LangGraph tras los puertos de
    Domain. Define las rutas determinísticas del workflow (rechazar, aclarar, recuperar
    evidencia, confirmar ticket); un LLM no define ni puede omitir estas políticas.

    Flujo: START -> analyze -> [reject | clarify | retrieve | confirm_ticket] -> ... -> END.
    """

    def __init__(self) -> None:
        maximum_clarification_attempts = ContextConfig().maximum_clarification_attempts
        self.maximum_clarification_attempts = maximum_clarification_attempts
        self.nodes = IncidentNodes(maximum_clarification_attempts)        
        checkpointer: BaseCheckpointSaver = Services.get_dependency(BaseCheckpointSaver)
        self.graph = self._build_graph(checkpointer)

    def _build_graph(self, checkpointer: BaseCheckpointSaver):
        workflow = StateGraph(IncidentState)  # type: ignore[bad-specialization]
        workflow.add_node("analyze", self.nodes.analyze_async)
        workflow.add_node("reject", self.nodes.prepare_rejection)
        workflow.add_node("prepare_clarification", self.nodes.prepare_clarification)
        workflow.add_node("pause_clarification", self.nodes.pause_for_clarification)
        workflow.add_node("retrieve_evidence", self.nodes.retrieve_evidence_async)
        workflow.add_node("build_response", self.nodes.build_response_async)
        workflow.add_node("prepare_ticket_confirmation", self.nodes.prepare_ticket_confirmation)
        workflow.add_node("pause_ticket_confirmation", self.nodes.pause_for_ticket_confirmation)
        workflow.add_node("create_ticket", self.nodes.create_ticket_async)
        workflow.add_node("close_without_ticket", self.nodes.close_without_ticket)
        workflow.add_edge(START, "analyze")
        workflow.add_conditional_edges("analyze", self.route_after_analysis, 
        {
            "reject": "reject", 
            "clarify": "prepare_clarification", 
            "retrieve": "retrieve_evidence", 
            "confirm_ticket": "prepare_ticket_confirmation"
        })
        workflow.add_edge("reject", END)
        workflow.add_edge("prepare_clarification", "pause_clarification")
        workflow.add_edge("pause_clarification", "analyze")
        workflow.add_conditional_edges("retrieve_evidence", self.route_after_evidence,
        {
            "respond": "build_response",
            "confirm_ticket": "prepare_ticket_confirmation"
        })
        workflow.add_edge("build_response", END)
        workflow.add_edge("prepare_ticket_confirmation", "pause_ticket_confirmation")
        workflow.add_conditional_edges("pause_ticket_confirmation", self.route_after_ticket_confirmation,
        {
            "create_ticket": "create_ticket", 
            "close_without_ticket": "close_without_ticket"
        })
        workflow.add_edge("create_ticket", END)
        workflow.add_edge("close_without_ticket", END)

        return workflow.compile(checkpointer=checkpointer)

    def route_after_analysis(self, state: IncidentState) -> Literal["reject", "clarify", "retrieve", "confirm_ticket"]:
        """Define la ruta tras el análisis del incidente.

        Reglas determinísticas (el LLM no las define):
        - Fuera de alcance -> reject.
        - Requiere aclaración y se superó el límite de intentos -> confirm_ticket.
        - Requiere aclaración y aún hay intentos -> clarify.
        - No requiere aclaración -> retrieve (buscar evidencia).
        """

        classification = state.get("classification", {})
        if not classification.get("in_scope", False):
            return "reject"
        if classification.get("requires_clarification", False):
            if state.get("clarification_attempts", 0) >= self.maximum_clarification_attempts:
                return "confirm_ticket"
            return "clarify"
        return "retrieve"

    def route_after_evidence(self, state: IncidentState) -> Literal["respond", "confirm_ticket"]:
        """Define la ruta tras recuperar evidencia.

        - Evidencia suficiente -> respond (generar respuesta final).
        - Evidencia insuficiente -> confirm_ticket (pedir autorización para escalar).
        
        Nunca se inventa una solución cuando la evidencia es insuficiente.
        """

        if state.get("evidence_status") == "sufficient":
            return "respond"
        return "confirm_ticket"

    def route_after_ticket_confirmation(self, state: IncidentState) -> Literal["create_ticket", "close_without_ticket"]:
        """Define la ruta tras la confirmación de ticket del usuario.

        - Confirmado -> create_ticket (solo tras confirmación explícita y del sistema externo).
        - Declinado -> close_without_ticket.
        """

        if state.get("ticket_confirmation") == "confirmed":
            return "create_ticket"
        return "close_without_ticket"

    async def ainvoke(self, graph_input: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta el grafo LangGraph.

        Soporta dos modos: invocación nueva (desde START) o reanudación de interrupción
        (Command resume con el mismo `thread_id` para continuar tras un `interrupt()`).
        """

        resume_input = graph_input.get("resume_input")
        if resume_input is not None:
            resume_value = dict(resume_input)
            resume_value.setdefault("message", graph_input.get("user_message", ""))
            state = await self.graph.ainvoke(Command(resume=resume_value), cast(RunnableConfig, config))
        else:
            state = await self.graph.ainvoke(graph_input, cast(RunnableConfig, config))
        return dict(state)
