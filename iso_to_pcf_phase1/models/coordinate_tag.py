from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


@dataclass
class CoordinateTag:
    id: str
    type: str = "coordinate_tag"
    attached_node: str = ""
    east: float | None = None
    north: float | None = None
    elevation: float | None = None
    source_text: str = ""
    unit: str = "mm"
    manual_verified: bool = True
    notes: str = ""
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoordinateTag":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
