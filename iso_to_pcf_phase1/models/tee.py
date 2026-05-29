from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data


TEE_TYPES = ["equal", "reducing", "unknown"]


@dataclass
class Tee:
    id: str
    type: str = "tee"
    center_node: str = ""
    run_in_segment: str = ""
    run_out_segment: str = ""
    branch_segment: str = ""
    tee_type: str = "unknown"
    manual_verified: bool = True
    notes: str = ""
    created_at: str = field(default_factory=current_timestamp)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tee":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)
