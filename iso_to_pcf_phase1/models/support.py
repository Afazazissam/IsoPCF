from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


@dataclass
class Support:
    id: str
    type: str = "support"
    support_node: str = ""
    host_segment: str = ""
    support_type: str = "unknown"
    distance_from_node: str = ""
    distance_value: float | None = None
    distance_unit: str = "mm"
    manual_verified: bool = True
    notes: str = ""
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Support":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
