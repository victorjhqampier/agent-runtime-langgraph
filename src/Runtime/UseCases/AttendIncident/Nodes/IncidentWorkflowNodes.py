from typing import Any

from langgraph.types import interrupt

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident
from Domain.Enums.IncidentStatus import IncidentStatus
from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Domain.ValueObjects.IncidentId import IncidentId
from Domain.ValueObjects.TenantId import TenantId
from Runtime.UseCases.AttendIncident.Prompts.IncidentReasoningPrompts import IncidentReasoningPrompts
from Runtime.UseCases.AttendIncident.States.IncidentState import IncidentState


class IncidentWorkflowNodes:
    def __init__(
        self,
        incident_reasoning: IIncidentReasoningCommand,
        evidence_query: IEvidenceQuery,
        ticket_command: ITicketCommand,
        ticket_query: ITicketQuery,
        prompts: IncidentReasoningPrompts,
        maximum_clarification_attempts: int,
    ) -> None:
        self.incident_reasoning = incident_reasoning
        self.evidence_query = evidence_query
        self.ticket_command = ticket_command
        self.ticket_query = ticket_query
        self.prompts = prompts
        self.maximum_clarification_attempts = maximum_clarification_attempts

    def build_incident(self, state: IncidentState) -> Incident:
        user_context = state.get("user_context", {})
        return Incident(
            id=IncidentId(state["turn_id"]),
            tenant_id=TenantId(str(user_context["tenant_id"])),
            session_id=state["session_id"],
            conversation_id=state["conversation_id"],
            description=state["user_message"],
            category=state.get("classification", {}).get("category"),
        )

    def build_search_incident(self, state: IncidentState) -> Incident:
        incident = self.build_incident(state)
        return Incident(
            id=incident.id,
            tenant_id=incident.tenant_id,
            session_id=incident.session_id,
            conversation_id=incident.conversation_id,
            description=str(state["classification"]["search_query"]),
            category=incident.category,
        )

    def build_evidence(self, documents: list[dict[str, Any]]) -> list[Evidence]:
        return [
            Evidence(
                document_id=str(document["document_id"]),
                content=str(document["content"]),
                version=document.get("version"),
                section=document.get("section"),
                authorized=bool(document.get("authorized")),
                current=bool(document.get("current")),
            )
            for document in documents
        ]

    def get_confirmation(self, resume_value: Any) -> bool | None:
        if isinstance(resume_value, dict):
            if isinstance(resume_value.get("confirmed"), bool):
                return resume_value["confirmed"]
            value = str(resume_value.get("message", "")).strip().lower()
        else:
            value = str(resume_value).strip().lower()
        if value in {"si", "sí", "yes", "confirmo", "confirmar", "créalo", "crealo"}:
            return True
        if value in {"no", "cancelar", "cancelo", "rechazo"}:
            return False
        return None

    async def analyze_async(self, state: IncidentState) -> dict[str, Any]:
        conversation_history = state.get("conversation_history", [])
        current_turn = {"role": "user", "content": state["user_message"]}
        history_for_analysis = [*conversation_history, current_turn]
        assessment = await self.incident_reasoning.analyze_async(self.build_incident(state), history_for_analysis, self.prompts.get_analysis_instructions())
        return {
            "conversation_history": [current_turn],
            "classification": {
                "in_scope": assessment.in_scope,
                "requires_clarification": assessment.requires_clarification,
                "clarification_question": assessment.clarification_question,
                "category": assessment.category,
                "search_query": assessment.search_query,
                "priority": assessment.priority.value,
            },
        }

    def prepare_rejection(self, state: IncidentState) -> dict[str, Any]:
        return {
            "resolution_status": "rejected",
            "response_text": "Este agente atiende incidentes de sistemas informáticos y mesa de ayuda. La solicitud corresponde a otro proceso.",
            "ticket": None,
            "interrupt": None,
            "voice_directives": {},
        }

    def prepare_clarification(self, state: IncidentState) -> dict[str, Any]:
        classification = state["classification"]
        attempts = state.get("clarification_attempts", 0) + 1
        question = str(classification["clarification_question"])
        return {
            "clarification_attempts": attempts,
            "resolution_status": "needs_clarification",
            "response_text": question,
            "interrupt": {"type": "clarification", "thread_id": state["thread_id"], "requested_fields": ["message"]},
            "voice_directives": {},
        }

    def pause_for_clarification(self, state: IncidentState) -> dict[str, Any]:
        resume_value = interrupt(state["interrupt"])
        if isinstance(resume_value, dict):
            message = str(resume_value.get("message", "")).strip()
        else:
            message = str(resume_value).strip()
        while not message:
            resume_value = interrupt(state["interrupt"])
            if isinstance(resume_value, dict):
                message = str(resume_value.get("message", "")).strip()
            else:
                message = str(resume_value).strip()
        return {"user_message": message, "resume_input": {"message": message}, "interrupt": None}

    async def retrieve_evidence_async(self, state: IncidentState) -> dict[str, Any]:
        evidence = await self.evidence_query.retrieve_async(self.build_search_incident(state))
        usable_evidence = [item for item in evidence if item.is_usable]
        documents = [
            {
                "document_id": item.document_id,
                "content": item.content,
                "version": item.version,
                "section": item.section,
                "authorized": item.authorized,
                "current": item.current,
            }
            for item in usable_evidence
        ]
        evidence_status = "sufficient" if documents else "insufficient"
        evidence_reason = "authorized_evidence_found" if documents else "no_authorized_current_evidence"
        return {
            "search_query": state["classification"]["search_query"],
            "search_attempts": state.get("search_attempts", 0) + 1,
            "retrieved_documents": documents,
            "evidence_status": evidence_status,
            "evidence_reason": evidence_reason,
            "citations": [{"document_id": item["document_id"], "version": item["version"], "section": item["section"]} for item in documents],
        }

    async def build_response_async(self, state: IncidentState) -> dict[str, Any]:
        response_text = await self.incident_reasoning.generate_response_async(
            self.build_incident(state), self.build_evidence(state.get("retrieved_documents", [])), self.prompts.get_response_instructions()
        )
        return {
            "resolution_status": "resolved",
            "response_text": response_text.strip(),
            "ticket": None,
            "interrupt": None,
            "voice_directives": {},
        }

    def prepare_ticket_confirmation(self, state: IncidentState) -> dict[str, Any]:
        reason = "No encontré documentación suficiente para resolver el incidente."
        if state.get("clarification_attempts", 0) >= self.maximum_clarification_attempts:
            reason = "No tengo información suficiente para identificar el incidente."
        return {
            "ticket_confirmation": "pending",
            "resolution_status": "needs_clarification",
            "response_text": f"{reason} ¿Deseas que cree un ticket para que el equipo lo revise?",
            "interrupt": {"type": "ticket_confirmation", "thread_id": state["thread_id"], "requested_fields": ["confirmed"]},
            "voice_directives": {},
        }

    def pause_for_ticket_confirmation(self, state: IncidentState) -> dict[str, Any]:
        confirmation = self.get_confirmation(interrupt(state["interrupt"]))
        while confirmation is None:
            confirmation = self.get_confirmation(interrupt(state["interrupt"]))
        return {"ticket_confirmation": "confirmed" if confirmation else "declined", "interrupt": None}

    async def create_ticket_async(self, state: IncidentState) -> dict[str, Any]:
        incident = self.build_incident(state)
        incident.escalate()
        idempotency_key = str(state.get("idempotency_key") or state["turn_id"])
        ticket = await self.ticket_query.get_by_idempotency_async(idempotency_key)
        if ticket is None:
            ticket = await self.ticket_command.create_async(incident, idempotency_key)
        return {
            "resolution_status": "escalated",
            "ticket": {"ticket_id": ticket.ticket_id, "status": ticket.status},
            "response_text": f"El ticket {ticket.ticket_id} fue creado correctamente.",
            "interrupt": None,
            "voice_directives": {},
        }

    def close_without_ticket(self, state: IncidentState) -> dict[str, Any]:
        return {
            "resolution_status": "resolved",
            "ticket_confirmation": "declined",
            "ticket": None,
            "response_text": "Entendido. No crearé ningún ticket. Puedes retomar este incidente cuando lo necesites.",
            "interrupt": None,
            "voice_directives": {},
        }
