from dataclasses import dataclass

from Domain.Enums.IncidentPriority import IncidentPriority


@dataclass(frozen=True, slots=True)
class IncidentAssessment:
    in_scope: bool
    requires_clarification: bool
    clarification_question: str | None = None
    category: str | None = None
    search_query: str | None = None
    priority: IncidentPriority = IncidentPriority.NORMAL

    def __post_init__(self) -> None:
        if self.requires_clarification and (self.clarification_question is None or not self.clarification_question.strip()):
            raise ValueError("An assessment requiring clarification must provide a question")
        if self.in_scope and not self.requires_clarification and (self.search_query is None or not self.search_query.strip()):
            raise ValueError("An assessable incident must provide an evidence search query")
