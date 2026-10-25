from Runtime.Internals.Adapters.ValidationResultAdapter import ValidationResultAdapter
from Runtime.Internals.Validators.ArifyValidator import ArifyValidator
from Runtime.Internals.Validators.ArifyValidatorBuilder import ArifyValidationRuleResponse
from typing import List, TypeVar, Callable


# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Fluent executor Class to standardize success and failure responses
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 31/01/2026
# *
# **********************************************************************************************************

T = TypeVar("T")


class FluentValidationExecutor:
    @staticmethod
    def execute(input_obj: T, validator_factory: Callable[[T], ArifyValidator]) -> List[ValidationResultAdapter]:
        try:
            validator: ArifyValidator = validator_factory(input_obj)
            errors: List[ArifyValidationRuleResponse] = validator.validate()

            result: List[ValidationResultAdapter] = []
            for error in errors:
                code: str = (error.error_code or "VALIDATION_ERROR").strip()
                msg: str = (error.message or "Invalid value").strip()
                field: str | None = error.field_name or None
                if field is not None:
                    field = field.strip() or None

                result.append(
                    ValidationResultAdapter(
                        Code=code,
                        Message=msg,
                        Field=field,
                    )
                )

            return result
        except Exception as e:
            # En caso de error en la validación, retornar un error genérico pi pi pi, no quiero usar try catch en otros lados
            return [ValidationResultAdapter(Code="VALIDATION_EXECUTOR_ERROR", Message=f"Error during validation: {str(e)}", Field=None)]
