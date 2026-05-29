from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


DIMENSION_KINDS = [
    "linear",
    "east_west",
    "north_south",
    "elevation",
    "slope",
    "angle",
    "unknown",
]


@dataclass
class Dimension:
    id: str
    type: str = "dimension"
    from_node: str = ""
    to_node: str = ""
    value: float | None = None
    unit: str = "mm"
    dimension_kind: str = "linear"
    source_text: str = ""
    page_number: int = 1
    manual_verified: bool = True
    notes: str = ""
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dimension":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
