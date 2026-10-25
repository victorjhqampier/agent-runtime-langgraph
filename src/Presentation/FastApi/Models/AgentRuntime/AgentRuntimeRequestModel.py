from typing import Optional
from pydantic import BaseModel, ConfigDict
from Runtime.Internals.Validators.ArifyValidator import ArifyValidator
from Runtime.Internals.Validators.ArifyValidatorBuilder import ArifyValidationRuleResponse, FieldValidator
from Presentation.FastApi.Models.AgentRuntime.AgentResumeInputModel import AgentResumeInputModel


class AgentRuntimeRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    SessionId: Optional[str] = None
    ConversationId: Optional[str] = None
    Message: Optional[str] = None
    Channel: Optional[str] = None
    ResumeInput: Optional[AgentResumeInputModel] = None


class AgentRuntimeRequestModelValidator(ArifyValidator):
    def __init__(self, x: AgentRuntimeRequestModel) -> None:
        super().__init__()

        self.add_rules(
            FieldValidator.from_object(x, "SessionId")
            .not_null()
            .with_code("SESSION_ID_REQUIRED")
            .with_message("SessionId is required")
            .not_empty()
            .with_code("SESSION_ID_EMPTY")
            .with_message("SessionId cannot be empty")
            .min_length(5)
            .with_code("SESSION_ID_MIN_LENGTH")
            .with_message("SessionId must have at least 5 characters")
            .max_length(42)
            .with_code("SESSION_ID_MAX_LENGTH")
            .with_message("SessionId cannot exceed 42 characters")
            .validate()
        )

        self.add_rules(
            FieldValidator.from_object(x, "ConversationId")
            .not_null()
            .with_code("CONVERSATION_ID_REQUIRED")
            .with_message("ConversationId is required")
            .not_empty()
            .with_code("CONVERSATION_ID_EMPTY")
            .with_message("ConversationId cannot be empty")
            .min_length(5)
            .with_code("CONVERSATION_ID_MIN_LENGTH")
            .with_message("ConversationId must have at least 5 characters")
            .max_length(42)
            .with_code("CONVERSATION_ID_MAX_LENGTH")
            .with_message("ConversationId cannot exceed 42 characters")
            .validate()
        )

        self.add_rules(
            FieldValidator.from_object(x, "Message")
            .not_null()
            .with_code("MESSAGE_REQUIRED")
            .with_message("Message is required")
            .not_empty()
            .with_code("MESSAGE_EMPTY")
            .with_message("Message cannot be empty")
            .max_length(20000)
            .with_code("MESSAGE_MAX_LENGTH")
            .with_message("Message cannot exceed 20000 characters")
            .validate()
        )

        self.add_rules(
            FieldValidator.from_object(x, "Channel")
            .not_null()
            .with_code("CHANNEL_REQUIRED")
            .with_message("Channel is required")
            .not_empty()
            .with_code("CHANNEL_EMPTY")
            .with_message("Channel cannot be empty")
            .validate()
        )

        if x.Channel is not None and x.Channel not in {"text", "voice"}:
            self.add_rules([ArifyValidationRuleResponse("Channel", "CHANNEL_INVALID", "Channel must be text or voice")])
