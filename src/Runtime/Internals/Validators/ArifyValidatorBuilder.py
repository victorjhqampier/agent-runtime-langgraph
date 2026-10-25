from typing import Any, List, Optional
# ********************************************************************************************************
# * Copyright © 2025 Arify Labs- All rights reserved.
# *
# * Info                  : Backend.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : -| victorjhampier@gmail.com | 968991*14
# *
# * Creation date         : 18/08/2024
# *
# **********************************************************************************************************


class ArifyValidationRuleResponse:
    def __init__(self, field_name: str, error_code: str, message: str):
        self.field_name: str = field_name
        self.error_code: str = error_code
        self.message: str = message

    def __repr__(self) -> str:
        return f"ArifyValidationRuleResponse(field_name={self.field_name!r}, error_code={self.error_code!r}, message={self.message!r})"


class FieldValidator:
    """
    Builder de validación para un campo específico,
    permitiendo encadenar reglas estilo FluentValidation.

    Ejemplo de uso:
        validator = FieldValidator("nombre", "   ")
        broken_rules = (
            validator
                .not_null()
                .not_empty()
                .min_length(3)
                .validate()
        )
    """

    def __init__(self, field_name: str, value: Any):
        self.__field_name: str = field_name
        self.__obj_field: Any = value
        self.__broken_rules: List[ArifyValidationRuleResponse] = []
        self.__current_rule: Optional[ArifyValidationRuleResponse] = None

    @classmethod
    def from_object(cls, obj: Any, field_name: str) -> "FieldValidator":
        """
        Sobrecarga simulada (similar a un segundo constructor).
        Crea un FieldValidator extrayendo el atributo 'field_name' de 'obj'.
        """
        value = getattr(obj, field_name, None)
        return cls(field_name, value)

    @classmethod
    def for_value(cls, value: Any, alias: Optional[str] = None) -> "FieldValidator":
        """
        Sobrecarga simulada adicional:
        Crea un FieldValidator para el 'value' con un nombre de campo ('alias') opcional
        """
        if not alias:
            alias = "unknown_field"
        return cls(alias, value)

    def append_rule(self, error_code: str, message: str) -> None:
        """
        Crea y agrega una nueva regla rota a la lista interna de reglas.
        """
        self.__current_rule = ArifyValidationRuleResponse(field_name=self.__field_name, error_code=error_code, message=message)
        self.__broken_rules.append(self.__current_rule)

    # -----------------------
    #   Métodos de validación
    # -----------------------

    def not_null(self) -> "FieldValidator":
        if self.__obj_field is None:
            self.append_rule("not_null", "No puede ser nulo.")
        else:
            self.__current_rule = None
        return self

    def not_empty(self) -> "FieldValidator":
        if self.__obj_field is None:
            # Si quisieras considerarlo vacío, podrías asignar un error aquí.
            # Pero normalmente, 'not_null()' es la encargada.
            self.__current_rule = None
            return self

        if isinstance(self.__obj_field, str):
            if self.__obj_field.strip() == "":
                self.append_rule("not_empty", "No puede estar vacío (string).")
            else:
                self.__current_rule = None

        elif isinstance(self.__obj_field, (list, dict, set, tuple)):
            if len(self.__obj_field) == 0:
                self.append_rule("not_empty", "No puede estar vacío (colección).")
            else:
                self.__current_rule = None

        else:
            self.__current_rule = None

        return self

    def min_length(self, min_len: int) -> "FieldValidator":
        if isinstance(self.__obj_field, str) and len(self.__obj_field) < min_len:
            self.append_rule("min_length", f"Debe tener al menos {min_len} caracteres.")
        else:
            self.__current_rule = None
        return self

    def max_length(self, max_len: int) -> "FieldValidator":
        if isinstance(self.__obj_field, str) and len(self.__obj_field) > max_len:
            self.append_rule("max_length", f"No puede tener más de {max_len} caracteres.")
        else:
            self.__current_rule = None
        return self

    def is_numeric(self) -> "FieldValidator":
        if not (isinstance(self.__obj_field, str) and self.__obj_field.isdigit()):
            self.append_rule("is_numeric", "Debe ser una cadena que contenga solo números.")
        else:
            self.__current_rule = None
        return self

    # -----------------------
    #   Métodos de personalización
    # -----------------------

    def with_message(self, custom_message: str) -> "FieldValidator":
        """
        Reemplaza el mensaje de la última regla rota (si existe) con uno personalizado.
        """
        if self.__current_rule:
            self.__current_rule.message = custom_message
        return self

    def with_code(self, custom_code: str) -> "FieldValidator":
        """
        Reemplaza el código de error de la última regla rota (si existe) con uno personalizado.
        """
        if self.__current_rule:
            self.__current_rule.error_code = custom_code
        return self

    def when(self, condition: bool) -> "FieldValidator":
        """
        Equivalente a 'When(...)' en FluentValidation:

        :param condition: Si es False, se descarta la última regla.
        """
        if not condition and self.__current_rule:
            if self.__current_rule in self.__broken_rules:
                self.__broken_rules.remove(self.__current_rule)
            self.__current_rule = None
        return self

    def validate(self) -> List[ArifyValidationRuleResponse]:
        """
        Retorna la lista de reglas rotas detectadas durante las validaciones encadenadas.
        """
        return self.__broken_rules
