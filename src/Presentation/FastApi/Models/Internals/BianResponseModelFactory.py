from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, create_model

T = TypeVar("T", bound=BaseModel)

_ADAPTER_SUFFIX = "Adapter"
_HELPER_SUFFIX = "Helper"
_RESPONSE_SUFFIX = "Response"

_model_cache: Dict[Type[BaseModel], Type[BaseModel]] = {}


def _get_base_name(type_name: str) -> str:
    if type_name.endswith(_RESPONSE_SUFFIX):
        name_wo_response = type_name[: -len(_RESPONSE_SUFFIX)]
        if name_wo_response.endswith(_ADAPTER_SUFFIX):
            return name_wo_response[: -len(_ADAPTER_SUFFIX)]
        return name_wo_response

    if type_name.endswith(_ADAPTER_SUFFIX):
        return type_name[: -len(_ADAPTER_SUFFIX)]

    if type_name.endswith(_HELPER_SUFFIX):
        return type_name[: -len(_HELPER_SUFFIX)]

    return type_name


def _generate_response_field_name(adapter_type: Type[T]) -> str:
    type_name = adapter_type.__name__
    base_name = _get_base_name(type_name)
    return base_name + _RESPONSE_SUFFIX


class BianResponseModelFactory:
    @staticmethod
    def success(adapter_type: Type[T]) -> Type[BaseModel]:
        if adapter_type in _model_cache:
            return _model_cache[adapter_type]

        field_name = _generate_response_field_name(adapter_type)
        model_name = f"Bian{field_name}Model"

        field_definitions: dict[str, Any] = {field_name: (Optional[adapter_type], None)}
        dynamic_model = create_model(model_name, **field_definitions)

        _model_cache[adapter_type] = dynamic_model
        return dynamic_model
