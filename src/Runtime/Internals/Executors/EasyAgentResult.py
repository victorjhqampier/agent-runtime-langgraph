from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from Runtime.Internals.Adapters.ValidationResultAdapter import ValidationResultAdapter

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : EasyAgentResult to standardize agent success and failure responses
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 31/01/2026
# *
# **********************************************************************************************************

T = TypeVar("T")
# Constante para evitar crear listas vacías repetidamente
_EMPTY_VALIDATIONS: list[ValidationResultAdapter] = []


@dataclass(frozen=True, slots=True)
class EasyAgentResult(Generic[T]):
    is_success: bool
    response: Optional[T] = None
    errors: list[ValidationResultAdapter] = field(default_factory=lambda: _EMPTY_VALIDATIONS)

    @classmethod
    def success(cls, response: T) -> "EasyAgentResult[T]":
        return cls(
            is_success=True,
            response=response,
            errors=_EMPTY_VALIDATIONS,
        )

    @classmethod
    def failure(cls, errors: list[ValidationResultAdapter]) -> "EasyAgentResult[T]":
        return cls(
            is_success=False,
            response=None,
            errors=errors or _EMPTY_VALIDATIONS,
        )
