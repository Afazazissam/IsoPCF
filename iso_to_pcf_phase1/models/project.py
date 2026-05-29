from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._helpers import current_timestamp, dataclass_to_dict, filtered_init_data
from .coordinate_tag import CoordinateTag
from .dimension import Dimension
from .elbow import Elbow
from .node import Node
from .pipe_segment import PipeSegment
from .support import Support
from .tee import Tee


@dataclass
class PageInfo:
    page_number: int
    width: float
    height: float
    rotation: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PageInfo":
        return cls(**filtered_init_data(cls, data))

    def to_dict(self) -> dict[str, Any]:
        return dataclass_to_dict(self)


@dataclass
class Project:
    project_name: str
    application: str = "AI-Assisted Isometric-to-PCF Generator"
    phase: str = "1"
    drawing_file: str = ""
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)
    units: str = "mm"
    pages: list[PageInfo] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    pipe_segments: list[PipeSegment] = field(default_factory=list)
    elbows: list[Elbow] = field(default_factory=list)
    tees: list[Tee] = field(default_factory=list)
    supports: list[Support] = field(default_factory=list)
    dimensions: list[Dimension] = field(default_factory=list)
    coordinate_tags: list[CoordinateTag] = field(default_factory=list)
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "manual_verified": True,
            "training_ready": True,
            "notes": "",
        }
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        project = cls(
            project_name=data.get("project_name", "Untitled Reconstruction"),
            application=data.get("application", "AI-Assisted Isometric-to-PCF Generator"),
            phase=str(data.get("phase", "1")),
            drawing_file=data.get("drawing_file", ""),
            created_at=data.get("created_at", current_timestamp()),
            updated_at=data.get("updated_at", current_timestamp()),
            units=data.get("units", "mm"),
            metadata=data.get(
                "metadata",
                {"manual_verified": True, "training_ready": True, "notes": ""},
            )
            or {"manual_verified": True, "training_ready": True, "notes": ""},
        )
        project.pages = [PageInfo.from_dict(item) for item in data.get("pages", [])]
        project.nodes = [Node.from_dict(item) for item in data.get("nodes", [])]
        project.pipe_segments = [
            PipeSegment.from_dict(item) for item in data.get("pipe_segments", [])
        ]
        project.elbows = [Elbow.from_dict(item) for item in data.get("elbows", [])]
        project.tees = [Tee.from_dict(item) for item in data.get("tees", [])]
        project.supports = [Support.from_dict(item) for item in data.get("supports", [])]
        project.dimensions = [
            Dimension.from_dict(item) for item in data.get("dimensions", [])
        ]
        project.coordinate_tags = [
            CoordinateTag.from_dict(item) for item in data.get("coordinate_tags", [])
        ]
        return project

    def touch(self) -> None:
        self.updated_at = current_timestamp()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "application": self.application,
            "phase": self.phase,
            "drawing_file": self.drawing_file,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "units": self.units,
            "pages": [page.to_dict() for page in self.pages],
            "nodes": [node.to_dict() for node in self.nodes],
            "pipe_segments": [segment.to_dict() for segment in self.pipe_segments],
            "elbows": [elbow.to_dict() for elbow in self.elbows],
            "tees": [tee.to_dict() for tee in self.tees],
            "supports": [support.to_dict() for support in self.supports],
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "coordinate_tags": [tag.to_dict() for tag in self.coordinate_tags],
            "metadata": self.metadata,
        }
