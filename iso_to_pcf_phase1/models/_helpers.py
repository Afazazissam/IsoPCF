from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime
from typing import Any, TypeVar


T = TypeVar("T")


def current_timestamp() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def filtered_init_data(model_type: type[T], data: dict[str, Any]) -> dict[str, Any]:
    allowed = {field.name for field in fields(model_type)}
    return {key: value for key, value in data.items() if key in allowed}


def dataclass_to_dict(instance: object) -> dict[str, Any]:
    return asdict(instance)
