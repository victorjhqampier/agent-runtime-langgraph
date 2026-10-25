from typing import Any, Dict, List
from Runtime.Internals.Validators.ArifyValidatorBuilder import ArifyValidationRuleResponse, FieldValidator


class ArifyValidator:
    def __init__(self):
        self._broken_rules: List[ArifyValidationRuleResponse] = []

    def get_field_name(self, obj, value) -> str:
        for field_name, field_value in obj.__dict__.items():
            if field_value is value:
                return field_name
        return ""

    def field(self, obj: Any, value: Any) -> FieldValidator:
        return FieldValidator(self.get_field_name(obj, value), value)

    def add_rules(self, rules: List[ArifyValidationRuleResponse]):
        self._broken_rules.extend(rules)

    def validate(self) -> List[ArifyValidationRuleResponse]:
        return self._broken_rules
