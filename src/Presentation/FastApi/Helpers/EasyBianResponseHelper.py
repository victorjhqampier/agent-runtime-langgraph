from Presentation.BusinessApi.Models.Internals.BianErrorInternalModel import BianErrorInternalModel
from Application.Internals.Adapters.ValidationResultAdapter import ValidationResultAdapter
from dataclasses import dataclass
from typing import Any, Dict, Type, ClassVar
from weakref import WeakKeyDictionary

# ********************************************************************************************************
# * Copyright � 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Easy BIAN Response Helper.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 01/01/2026
# *
# **********************************************************************************************************


class EasyBianResponseHelper:
    _response_field_name_cache: ClassVar["WeakKeyDictionary[type, str]"] = WeakKeyDictionary()

    # Constantes
    _ERRORS_KEY: ClassVar[str] = "errors"
    _DEFAULT_ERROR_CODE: ClassVar[str] = "1099"
    _DEFAULT_ERROR_MESSAGE: ClassVar[str] = "No es un problema de tu lado. Estamos experimentando dificultades técnicas"
    _GENERAL_FIELD: ClassVar[str] = "General"
    _IN_SEPARATOR: ClassVar[str] = " in "
    _ADAPTER_SUFFIX: ClassVar[str] = "Adapter"
    _HELPER_SUFFIX: ClassVar[str] = "Helper"
    _RESPONSE_SUFFIX: ClassVar[str] = "Response"

    @staticmethod
    def success_response(data: Any) -> Dict[str, Any]:
        field_name = EasyBianResponseHelper._get_response_field_name_from_object(data)
        return {field_name: data}

    @staticmethod
    def warning_response(validation_errors: list[ValidationResultAdapter]) -> Dict[str, Any]:
        # Prealocar lista del tamaño exacto (similar a array en C#)
        errors: list[BianErrorInternalModel] = [None] * len(validation_errors)  # type: ignore[list-item]
        i = 0

        for err in validation_errors:
            field_name = err.Field if err.Field else EasyBianResponseHelper._GENERAL_FIELD
            errors[i] = BianErrorInternalModel(
                Status_code=err.Code,
                Message=err.Message + EasyBianResponseHelper._IN_SEPARATOR + field_name,
            )
            i += 1

        return {EasyBianResponseHelper._ERRORS_KEY: errors}

    @staticmethod
    def error_response(error_code: str = _DEFAULT_ERROR_CODE, message: str = _DEFAULT_ERROR_MESSAGE) -> Dict[str, Any]:
        return {EasyBianResponseHelper._ERRORS_KEY: [BianErrorInternalModel(Status_code=error_code, Message=message)]}

    @staticmethod
    def easy_success_respond(data: Any) -> Dict[str, Any]:
        return EasyBianResponseHelper.success_response(data)

    @staticmethod
    def easy_warning_respond(validation_errors: list[ValidationResultAdapter]) -> Dict[str, Any]:
        return EasyBianResponseHelper.warning_response(validation_errors)

    @staticmethod
    def easy_error_respond(
        error_code: str = _DEFAULT_ERROR_CODE,
        message: str = _DEFAULT_ERROR_MESSAGE,
    ) -> Dict[str, Any]:
        return EasyBianResponseHelper.error_response(error_code, message)

    # ---- Internals ----
    @staticmethod
    def _get_response_field_name_from_object(data: Any) -> str:
        if data is None:
            return "data"

        t = type(data)
        cached = EasyBianResponseHelper._response_field_name_cache.get(t)
        if cached is not None:
            return cached

        name = EasyBianResponseHelper._generate_response_field_name(t)
        EasyBianResponseHelper._response_field_name_cache[t] = name
        return name

    @staticmethod
    def _generate_response_field_name(t: Type[Any]) -> str:
        type_name = t.__name__
        base_name = EasyBianResponseHelper._get_base_name(type_name)
        return base_name + EasyBianResponseHelper._RESPONSE_SUFFIX

    @staticmethod
    def _get_base_name(type_name: str) -> str:
        rs = EasyBianResponseHelper._RESPONSE_SUFFIX
        ad = EasyBianResponseHelper._ADAPTER_SUFFIX
        hs = EasyBianResponseHelper._HELPER_SUFFIX

        if type_name.endswith(rs):
            name_wo_response = type_name[: -len(rs)]
            if name_wo_response.endswith(ad):
                return name_wo_response[: -len(ad)]
            return name_wo_response

        if type_name.endswith(ad):
            return type_name[: -len(ad)]

        if type_name.endswith(hs):
            return type_name[: -len(hs)]

        return type_name
