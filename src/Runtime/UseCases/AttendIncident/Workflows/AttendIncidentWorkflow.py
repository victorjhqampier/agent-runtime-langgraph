from typing import Any, Literal, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort
from Runtime.UseCases.AttendIncident.Nodes.IncidentWorkflowNodes import IncidentWorkflowNodes
from Runtime.UseCases.AttendIncident.Prompts.IncidentReasoningPrompts import IncidentReasoningPrompts
from Runtime.UseCases.AttendIncident.States.IncidentState import IncidentState


class AttendIncidentWorkflow(IRuntimeGraphPort):
    def __init__(
        self,
        incident_reasoning: IIncidentReasoningCommand,
        evidence_query: IEvidenceQuery,
        ticket_command: ITicketCommand,
        ticket_query: ITicketQuery,
        checkpointer: BaseCheckpointSaver,
        maximum_clarification_attempts: int = 2,
    ) -> None:
        self.nodes = IncidentWorkflowNodes(incident_reasoning, evidence_query, ticket_command, ticket_query, IncidentReasoningPrompts(), maximum_clarification_attempts)
        self.maximum_clarification_attempts = maximum_clarification_attempts
        self.graph = self.build_graph(checkpointer)

    def build_graph(self, checkpointer: BaseCheckpointSaver):
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
        workflow.add_conditional_edges(
            "analyze",
            self.route_after_analysis,
            {"reject": "reject", "clarify": "prepare_clarification", "retrieve": "retrieve_evidence", "confirm_ticket": "prepare_ticket_confirmation"},
        )
        workflow.add_edge("reject", END)
        workflow.add_edge("prepare_clarification", "pause_clarification")
        workflow.add_edge("pause_clarification", "analyze")
        workflow.add_conditional_edges("retrieve_evidence", self.route_after_evidence, {"respond": "build_response", "confirm_ticket": "prepare_ticket_confirmation"})
        workflow.add_edge("build_response", END)
        workflow.add_edge("prepare_ticket_confirmation", "pause_ticket_confirmation")
        workflow.add_conditional_edges(
            "pause_ticket_confirmation", self.route_after_ticket_confirmation, {"create_ticket": "create_ticket", "close_without_ticket": "close_without_ticket"}
        )
        workflow.add_edge("create_ticket", END)
        workflow.add_edge("close_without_ticket", END)
        return workflow.compile(checkpointer=checkpointer)

    def route_after_analysis(self, state: IncidentState) -> Literal["reject", "clarify", "retrieve", "confirm_ticket"]:
        classification = state.get("classification", {})
        if not classification.get("in_scope", False):
            return "reject"
        if classification.get("requires_clarification", False):
            if state.get("clarification_attempts", 0) >= self.maximum_clarification_attempts:
                return "confirm_ticket"
            return "clarify"
        return "retrieve"

    def route_after_evidence(self, state: IncidentState) -> Literal["respond", "confirm_ticket"]:
        if state.get("evidence_status") == "sufficient":
            return "respond"
        return "confirm_ticket"

    def route_after_ticket_confirmation(self, state: IncidentState) -> Literal["create_ticket", "close_without_ticket"]:
        if state.get("ticket_confirmation") == "confirmed":
            return "create_ticket"
        return "close_without_ticket"

    async def ainvoke(self, graph_input: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        resume_input = graph_input.get("resume_input")
        if resume_input is not None:
            resume_value = dict(resume_input)
            resume_value.setdefault("message", graph_input.get("user_message", ""))
            state = await self.graph.ainvoke(Command(resume=resume_value), cast(RunnableConfig, config))
        else:
            state = await self.graph.ainvoke(graph_input, cast(RunnableConfig, config))
        return dict(state)
