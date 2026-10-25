from Presentation.BusinessApi.Models.Internals.FieldErrorInternalModel import FieldErrorInternalModel
from Application.Internals.Adapters.ValidationResultAdapter import ValidationResultAdapter
from Presentation.BusinessApi.Models.Internals.ResponseInternalModel import ResponseInternalModel
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, Sequence, Type, TypeVar

# ********************************************************************************************************
# * Copyright © 2026 Arify Labs - All rights reserved.
# *
# * Info                  : Easy Response Helper.
# *
# * By                    : Victor Jhampier Caxi Maquera
# * Email/Mobile/Phone    : victorjhampier@gmail.com | 968991714
# *
# * Creation date         : 01/01/2026
# *
# **********************************************************************************************************
T = TypeVar("T")
TResponse = TypeVar("TResponse", bound="ResponseInternalModel")


class EasyResponseHelper:
    # Cache para "propiedad destino" por tipo de respuesta (equivalente a ConcurrentDictionary<Type, PropertyInfo?>)
    _property_cache: Dict[type, Optional[str]] = {}

    @staticmethod
    def error_response(error_code: str, message: str = "Error general interno") -> ResponseInternalModel:
        return ResponseInternalModel(Errors=[FieldErrorInternalModel(StatusCode=error_code, Message=message)])

    @staticmethod
    def warning_response(error_list: list[ValidationResultAdapter]) -> ResponseInternalModel:
        # Prealocar lista del tamaño exacto (similar a new List<>(Count))
        errors: list[FieldErrorInternalModel] = [None] * len(error_list)  # type: ignore[list-item]
        i = 0
        for e in error_list:
            errors[i] = FieldErrorInternalModel(StatusCode=e.Code, Message=e.Message, Field=e.Field)
            i += 1
        return ResponseInternalModel(Errors=errors)

    @staticmethod
    def success_response(data_response: T) -> ResponseInternalModel:
        return ResponseInternalModel(Response=data_response)

    @staticmethod
    def success_response_typed(response_type: Type[TResponse], data_response: Any) -> TResponse:
        """
        Equivalente a:
          public static TResponse SuccessResponse<TResponse>(object dataResponse)
          where TResponse : ResponseInternalModel, new()
        """
        result = response_type()  # requiere constructor sin args (como new())

        attr = EasyResponseHelper._property_cache.get(response_type)
        if attr is None and response_type not in EasyResponseHelper._property_cache:
            attr = EasyResponseHelper._find_target_attr(response_type)
            EasyResponseHelper._property_cache[response_type] = attr

        if attr:
            setattr(result, attr, data_response)

        return result

    @staticmethod
    def _find_target_attr(response_type: Type[TResponse]) -> Optional[str]:
        exclude = {"statuscode", "errors"}

        # 1) Si el tipo tiene __annotations__ (dataclasses / pydantic), úsalo: es lo más barato/estable
        ann = getattr(response_type, "__annotations__", None)
        if ann:
            for name in ann.keys():
                if name.lower() not in exclude:
                    return name

        # 2) Fallback: inspeccionar atributos de clase (evita reflection pesada)
        for name in dir(response_type):
            if name.startswith("_"):
                continue
            if name.lower() in exclude:
                continue
            # evitar métodos/propiedades no settable (best effort)
            val = getattr(response_type, name, None)
            if callable(val):
                continue
            return name

        return None
