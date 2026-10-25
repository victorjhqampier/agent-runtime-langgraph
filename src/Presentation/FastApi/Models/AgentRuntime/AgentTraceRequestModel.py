from Runtime.Internals.Validators.ArifyValidator import ArifyValidator
from Runtime.Internals.Validators.ArifyValidatorBuilder import FieldValidator
from pydantic import BaseModel
from typing import Optional


class AgentTraceRequestModel(BaseModel):
    device_identifier: Optional[str] = None
    message_identifier: Optional[str] = None
    channel_identifier: Optional[str] = None
    session_identifier: Optional[str] = None

class AgentTraceRequestModelValidator(ArifyValidator):
    def __init__(self, x: AgentTraceRequestModel) -> None:
        super().__init__()

        self.add_rules(
            FieldValidator.from_object(x, "device_identifier")
            .not_null()
            .with_code("21001")
            .with_message("Cannot be null")
            .not_empty()
            .with_code("21002")
            .with_message("Cannot be empty")
            .min_length(5)
            .with_code("21004")
            .with_message("Allowed minimum length")
            .max_length(42)
            .with_code("21005")
            .with_message("Allowed maximum length")
            .validate()
        )

        self.add_rules(
            FieldValidator.from_object(x, "message_identifier")
            .not_null()
            .with_code("21001")
            .with_message("Cannot be null")
            .not_empty()
            .with_code("21002")
            .with_message("Cannot be empty")
            .min_length(7)
            .with_code("21004")
            .with_message("Allowed minimum length")
            .max_length(36)
            .with_code("21005")
            .with_message("Allowed maximum length")
            .validate()
        )

        self.add_rules(
            FieldValidator.from_object(x, "channel_identifier")
            .not_null()
            .with_code("21001")
            .with_message("Cannot be null")
            .not_empty()
            .with_code("21002")
            .with_message("Cannot be empty")
            .min_length(5)
            .with_code("21004")
            .with_message("Allowed minimum length")
            .max_length(42)
            .with_code("21005")
            .with_message("Allowed maximum length")
            .validate()
        )

        self.add_rules(
                    FieldValidator.from_object(x, "session_identifier")
                    .not_null()
                    .with_code("21001")
                    .with_message("Cannot be null")
                    .not_empty()
                    .with_code("21002")
                    .with_message("Cannot be empty")
                    .min_length(5)
                    .with_code("21004")
                    .with_message("Allowed minimum length")
                    .max_length(42)
                    .with_code("21005")
                    .with_message("Allowed maximum length")
                    .validate()
                )
