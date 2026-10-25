import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from langgraph.checkpoint.memory import InMemorySaver

from Domain.Entities.Evidence import Evidence
from Domain.Entities.Incident import Incident
from Domain.Entities.IncidentAssessment import IncidentAssessment
from Domain.Entities.Ticket import Ticket
from Domain.Enums.IncidentPriority import IncidentPriority
from Domain.Interfaces.Commands.IIncidentReasoningCommand import IIncidentReasoningCommand
from Domain.Interfaces.Commands.ITicketCommand import ITicketCommand
from Domain.Interfaces.Queries.IEvidenceQuery import IEvidenceQuery
from Domain.Interfaces.Queries.ITicketQuery import ITicketQuery
from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.UseCases.AttendIncident.AttendIncidentUsecase import AttendIncidentUsecase
from Runtime.UseCases.AttendIncident.Schemas.UserContext import UserContext
from Runtime.UseCases.AttendIncident.Workflows.AttendIncidentWorkflow import AttendIncidentWorkflow


class StubIncidentReasoningCommand(IIncidentReasoningCommand):
    def __init__(self, assessments: list[IncidentAssessment]) -> None:
        self.assessments = assessments
        self.analysis_calls = 0

    async def analyze_async(self, incident: Incident, conversation_history: list[dict[str, str]], instructions: str, cancellation_event=None) -> IncidentAssessment:
        assessment = self.assessments[min(self.analysis_calls, len(self.assessments) - 1)]
        self.analysis_calls += 1
        return assessment

    async def generate_response_async(self, incident: Incident, evidence: list[Evidence], instructions: str, cancellation_event=None) -> str:
        return "Aplica el procedimiento documentado para la VPN."


class StubEvidenceQuery(IEvidenceQuery):
    def __init__(self, evidence: list[Evidence]) -> None:
        self.evidence = evidence

    async def retrieve_async(self, incident: Incident) -> list[Evidence]:
        return self.evidence


class StubTicketCommand(ITicketCommand):
    def __init__(self) -> None:
        self.calls = 0

    async def create_async(self, incident: Incident, idempotency_key: str) -> Ticket:
        self.calls += 1
        return Ticket(ticket_id="INC-456", status="created")


class StubTicketQuery(ITicketQuery):
    def __init__(self, ticket: Ticket | None = None) -> None:
        self.ticket = ticket

    async def get_by_idempotency_async(self, idempotency_key: str) -> Ticket | None:
        return self.ticket


class AttendIncidentWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def build_input(self, message: str = "La VPN no conecta", resume_input: dict | None = None) -> dict:
        return {
            "session_id": "session-123",
            "conversation_id": "conversation-123",
            "thread_id": "thread-123",
            "correlation_id": "message-123",
            "turn_id": "message-123",
            "user_message": message,
            "user_context": {"user_id": "device-123", "tenant_id": "tenant-123"},
            "channel": "text",
            "idempotency_key": "message-123",
            "resume_input": resume_input,
        }

    def build_workflow(
        self, assessments: list[IncidentAssessment], evidence: list[Evidence], existing_ticket: Ticket | None = None
    ) -> tuple[AttendIncidentWorkflow, StubTicketCommand]:
        ticket_command = StubTicketCommand()
        return AttendIncidentWorkflow(
            StubIncidentReasoningCommand(assessments), StubEvidenceQuery(evidence), ticket_command, StubTicketQuery(existing_ticket), InMemorySaver()
        ), ticket_command

    def get_config(self) -> dict:
        return {"configurable": {"thread_id": "thread-123"}}

    async def test_documented_incident_resolves_in_the_first_turn(self) -> None:
        workflow, ticket_command = self.build_workflow(
            [IncidentAssessment(in_scope=True, requires_clarification=False, category="vpn", search_query="vpn disconnects", priority=IncidentPriority.NORMAL)],
            [Evidence(document_id="vpn-001", content="Reinicie el cliente VPN.", authorized=True, current=True)],
        )

        result = await workflow.ainvoke(self.build_input(), self.get_config())

        self.assertEqual("resolved", result["resolution_status"])
        self.assertEqual(0, ticket_command.calls)
        self.assertEqual("vpn-001", result["citations"][0]["document_id"])

    async def test_usecase_maps_workflow_state_to_runtime_response(self) -> None:
        workflow, _ = self.build_workflow(
            [IncidentAssessment(in_scope=True, requires_clarification=False, category="vpn", search_query="vpn disconnects", priority=IncidentPriority.NORMAL)],
            [Evidence(document_id="vpn-001", content="Reinicie el cliente VPN.", authorized=True, current=True)],
        )
        request = RuntimeRequestAdapter(
            session_id="session-123",
            conversation_id="conversation-123",
            thread_id="thread-123",
            correlation_id="message-123",
            turn_id="message-123",
            message="La VPN no conecta",
            channel="text",
            user_context=UserContext(user_id="device-123", tenant_id="tenant-123"),
            idempotency_key="message-123",
        )

        result = await AttendIncidentUsecase(workflow).execute_async(request)

        self.assertTrue(result.is_success)
        self.assertIsNotNone(result.response)
        self.assertEqual("resolved", result.response.status if result.response is not None else None)
        self.assertEqual("message-123", result.response.correlation_id if result.response is not None else None)

    async def test_ambiguous_incident_resumes_with_the_same_thread(self) -> None:
        workflow, _ = self.build_workflow(
            [
                IncidentAssessment(in_scope=True, requires_clarification=True, clarification_question="¿Qué servicio presenta el problema?"),
                IncidentAssessment(in_scope=True, requires_clarification=False, category="vpn", search_query="vpn", priority=IncidentPriority.NORMAL),
            ],
            [Evidence(document_id="vpn-001", content="Reinicie el cliente VPN.", authorized=True, current=True)],
        )

        paused = await workflow.ainvoke(self.build_input("No funciona"), self.get_config())
        result = await workflow.ainvoke(self.build_input("La VPN", {"message": "La VPN"}), self.get_config())

        self.assertEqual("needs_clarification", paused["resolution_status"])
        self.assertEqual("clarification", paused["interrupt"]["type"])
        self.assertEqual("resolved", result["resolution_status"])

    async def test_missing_evidence_creates_ticket_only_after_confirmation(self) -> None:
        workflow, ticket_command = self.build_workflow(
            [IncidentAssessment(in_scope=True, requires_clarification=False, category="application", search_query="XJ-9482", priority=IncidentPriority.NORMAL)],
            [],
        )

        paused = await workflow.ainvoke(self.build_input("Error XJ-9482"), self.get_config())
        result = await workflow.ainvoke(self.build_input("Sí, créalo", {"confirmed": True}), self.get_config())

        self.assertEqual("ticket_confirmation", paused["interrupt"]["type"])
        self.assertEqual("escalated", result["resolution_status"])
        self.assertEqual("INC-456", result["ticket"]["ticket_id"])
        self.assertEqual(1, ticket_command.calls)

    async def test_ticket_rejection_does_not_execute_external_action(self) -> None:
        workflow, ticket_command = self.build_workflow(
            [IncidentAssessment(in_scope=True, requires_clarification=False, category="application", search_query="XJ-9482", priority=IncidentPriority.NORMAL)],
            [],
        )

        await workflow.ainvoke(self.build_input("Error XJ-9482"), self.get_config())
        result = await workflow.ainvoke(self.build_input("No", {"confirmed": False}), self.get_config())

        self.assertEqual("resolved", result["resolution_status"])
        self.assertIsNone(result["ticket"])
        self.assertEqual(0, ticket_command.calls)

    async def test_existing_idempotency_ticket_is_reused_without_new_creation(self) -> None:
        workflow, ticket_command = self.build_workflow(
            [IncidentAssessment(in_scope=True, requires_clarification=False, category="application", search_query="XJ-9482", priority=IncidentPriority.NORMAL)],
            [],
            Ticket(ticket_id="INC-456", status="created"),
        )

        await workflow.ainvoke(self.build_input("Error XJ-9482"), self.get_config())
        result = await workflow.ainvoke(self.build_input("Sí, créalo", {"confirmed": True}), self.get_config())

        self.assertEqual("escalated", result["resolution_status"])
        self.assertEqual("INC-456", result["ticket"]["ticket_id"])
        self.assertEqual(0, ticket_command.calls)

    async def test_out_of_scope_request_is_rejected_without_external_calls(self) -> None:
        workflow, ticket_command = self.build_workflow([IncidentAssessment(in_scope=False, requires_clarification=False)], [])

        result = await workflow.ainvoke(self.build_input("Calcula el score de un cliente"), self.get_config())

        self.assertEqual("rejected", result["resolution_status"])
        self.assertEqual(0, ticket_command.calls)
