from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


NODE_ROLES = [
    "pipe_endpoint",
    "elbow_center",
    "tee_center",
    "reducer_center",
    "flange_center",
    "valve_center",
    "support_point",
    "instrument_point",
    "continuation_point",
    "dimension_reference",
    "coordinate_reference",
    "elevation_reference",
    "unknown",
]


@dataclass
class Node:
    id: str
    type: str = "node"
    node_role: str = "unknown"
    page_number: int = 1
    pdf_x: float = 0.0
    pdf_y: float = 0.0
    drawing_file: str = ""
    nearby_text: str = ""
    notes: str = ""
    manual_verified: bool = True
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Node":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
