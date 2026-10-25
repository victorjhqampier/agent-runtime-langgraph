from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from Runtime.Internals.Validators.ArifyValidator import ArifyValidator
from Runtime.Internals.Validators.ArifyValidatorBuilder import FieldValidator


class AgentResumeInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    Value: Optional[dict[str, Any]] = None

class AgentResumeInputModelValidator(ArifyValidator):
    def __init__(self, x: AgentResumeInputModel) -> None:
        super().__init__()

        self.add_rules(
            FieldValidator.from_object(x, "Value")
            .not_null()
            .with_code("RESUME_VALUE_REQUIRED")
            .with_message("Value is required when ResumeInput is provided")
            .not_empty()
            .with_code("RESUME_VALUE_EMPTY")
            .with_message("Value cannot be empty when ResumeInput is provided")
            .validate()
        )
