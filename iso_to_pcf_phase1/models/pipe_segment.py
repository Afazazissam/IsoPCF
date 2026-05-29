from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


@dataclass
class PipeSegment:
    id: str
    type: str = "pipe_segment"
    from_node: str = ""
    to_node: str = ""
    page_number: int = 1
    line_number: str = ""
    nominal_diameter: float | None = None
    spec: str = ""
    notes: str = ""
    manual_verified: bool = True
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipeSegment":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
