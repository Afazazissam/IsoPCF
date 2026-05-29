from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


RADIUS_TYPES = ["LR", "SR", "custom", "unknown"]


@dataclass
class Elbow:
    id: str
    type: str = "elbow"
    center_node: str = ""
    angle_deg: float = 90.0
    radius_type: str = "LR"
    radius_value: float | None = None
    incoming_segment: str = ""
    outgoing_segment: str = ""
    manual_verified: bool = True
    notes: str = ""
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Elbow":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
