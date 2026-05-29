from __future__ import annotations

from math import hypot
from pathlib import Path

from models.coordinate_tag import CoordinateTag
from models.dimension import Dimension
from models.elbow import Elbow
from models.node import Node
from models.pipe_segment import PipeSegment
from models.project import PageInfo, Project
from models.support import Support
from models.tee import Tee

from .id_generator import IdGenerator


class ReconstructionManager:
    def __init__(self) -> None:
        self.project = Project(project_name="Untitled Reconstruction")

    def new_project_for_pdf(self, pdf_path: str | Path, pages: list[PageInfo]) -> Project:
        path = Path(pdf_path)
        self.project = Project(
            project_name=f"{path.stem} Reconstruction",
            drawing_file=path.name,
            pages=pages,
            metadata={
                "manual_verified": True,
                "training_ready": True,
                "notes": "",
                "source_pdf_path": str(path),
            },
        )
        return self.project

    def set_project(self, project: Project) -> None:
        self.project = project

    def all_entity_ids(self) -> set[str]:
        return {
            *[item.id for item in self.project.nodes],
            *[item.id for item in self.project.pipe_segments],
            *[item.id for item in self.project.elbows],
            *[item.id for item in self.project.tees],
            *[item.id for item in self.project.supports],
            *[item.id for item in self.project.dimensions],
            *[item.id for item in self.project.coordinate_tags],
        }

    def add_node(
        self,
        *,
        node_role: str,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        nearby_text: str = "",
        notes: str = "",
    ) -> Node:
        node = Node(
            id=IdGenerator.next_id("N", {node.id for node in self.project.nodes}),
            node_role=node_role,
            page_number=page_number,
            pdf_x=round(pdf_x, 3),
            pdf_y=round(pdf_y, 3),
            drawing_file=self.project.drawing_file,
            nearby_text=nearby_text,
            notes=notes,
        )
        self.project.nodes.append(node)
        self.project.touch()
        return node

    def add_pipe_segment(
        self,
        *,
        from_node: str,
        to_node: str,
        line_number: str = "",
        nominal_diameter: float | None = None,
        spec: str = "",
        notes: str = "",
    ) -> PipeSegment:
        page_number = self.get_node(from_node).page_number if self.get_node(from_node) else 1
        segment = PipeSegment(
            id=IdGenerator.next_id("P", {item.id for item in self.project.pipe_segments}),
            from_node=from_node,
            to_node=to_node,
            page_number=page_number,
            line_number=line_number,
            nominal_diameter=nominal_diameter,
            spec=spec,
            notes=notes,
        )
        self.project.pipe_segments.append(segment)
        self.project.touch()
        return segment

    def add_elbow(
        self,
        *,
        center_node: str,
        angle_deg: float = 90.0,
        radius_type: str = "LR",
        radius_value: float | None = None,
        incoming_segment: str = "",
        outgoing_segment: str = "",
        notes: str = "",
    ) -> Elbow:
        elbow = Elbow(
            id=IdGenerator.next_id("E", {item.id for item in self.project.elbows}),
            center_node=center_node,
            angle_deg=angle_deg,
            radius_type=radius_type,
            radius_value=radius_value,
            incoming_segment=incoming_segment,
            outgoing_segment=outgoing_segment,
            notes=notes,
        )
        self.project.elbows.append(elbow)
        self.project.touch()
        return elbow

    def add_tee(
        self,
        *,
        center_node: str,
        run_in_segment: str = "",
        run_out_segment: str = "",
        branch_segment: str = "",
        tee_type: str = "unknown",
        notes: str = "",
    ) -> Tee:
        tee = Tee(
            id=IdGenerator.next_id("T", {item.id for item in self.project.tees}),
            center_node=center_node,
            run_in_segment=run_in_segment,
            run_out_segment=run_out_segment,
            branch_segment=branch_segment,
            tee_type=tee_type,
            notes=notes,
        )
        self.project.tees.append(tee)
        self.project.touch()
        return tee

    def add_support(
        self,
        *,
        support_node: str,
        host_segment: str,
        support_type: str = "unknown",
        distance_from_node: str = "",
        distance_value: float | None = None,
        distance_unit: str = "mm",
        notes: str = "",
    ) -> Support:
        support = Support(
            id=IdGenerator.next_id("S", {item.id for item in self.project.supports}),
            support_node=support_node,
            host_segment=host_segment,
            support_type=support_type,
            distance_from_node=distance_from_node,
            distance_value=distance_value,
            distance_unit=distance_unit,
            notes=notes,
        )
        self.project.supports.append(support)
        self.project.touch()
        return support

    def add_dimension(
        self,
        *,
        from_node: str,
        to_node: str,
        value: float | None,
        unit: str,
        dimension_kind: str,
        source_text: str,
        page_number: int,
        direction: str = "UNKNOWN",
        notes: str = "",
    ) -> Dimension:
        dimension = Dimension(
            id=IdGenerator.next_id("D", {item.id for item in self.project.dimensions}),
            from_node=from_node,
            to_node=to_node,
            value=value,
            unit=unit,
            dimension_kind=dimension_kind,
            direction=direction,
            source_text=source_text,
            page_number=page_number,
            notes=notes,
        )
        self.project.dimensions.append(dimension)
        self.project.touch()
        return dimension

    def add_coordinate_tag(
        self,
        *,
        attached_node: str,
        east: float | None,
        north: float | None,
        elevation: float | None,
        source_text: str,
        unit: str = "mm",
        notes: str = "",
    ) -> CoordinateTag:
        tag = CoordinateTag(
            id=IdGenerator.next_id("C", {item.id for item in self.project.coordinate_tags}),
            attached_node=attached_node,
            east=east,
            north=north,
            elevation=elevation,
            source_text=source_text,
            unit=unit,
            notes=notes,
        )
        self.project.coordinate_tags.append(tag)
        self.project.touch()
        return tag

    def get_node(self, node_id: str) -> Node | None:
        return next((node for node in self.project.nodes if node.id == node_id), None)

    def get_segment(self, segment_id: str) -> PipeSegment | None:
        return next(
            (segment for segment in self.project.pipe_segments if segment.id == segment_id),
            None,
        )

    def segments_for_node(self, node_id: str) -> list[PipeSegment]:
        return [
            segment
            for segment in self.project.pipe_segments
            if segment.from_node == node_id or segment.to_node == node_id
        ]

    def find_nearest_node(
        self,
        *,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        tolerance: float = 14.0,
    ) -> Node | None:
        candidates = [
            (hypot(node.pdf_x - pdf_x, node.pdf_y - pdf_y), node)
            for node in self.project.nodes
            if node.page_number == page_number
        ]
        if not candidates:
            return None
        distance, node = min(candidates, key=lambda item: item[0])
        return node if distance <= tolerance else None

    def find_nearest_segment(
        self,
        *,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        tolerance: float = 14.0,
    ) -> PipeSegment | None:
        candidates: list[tuple[float, PipeSegment]] = []
        for segment in self.project.pipe_segments:
            if segment.page_number != page_number:
                continue
            start = self.get_node(segment.from_node)
            end = self.get_node(segment.to_node)
            if not start or not end:
                continue
            distance = self._distance_to_segment(
                pdf_x,
                pdf_y,
                start.pdf_x,
                start.pdf_y,
                end.pdf_x,
                end.pdf_y,
            )
            candidates.append((distance, segment))
        if not candidates:
            return None
        distance, segment = min(candidates, key=lambda item: item[0])
        return segment if distance <= tolerance else None

    @staticmethod
    def _distance_to_segment(
        px: float,
        py: float,
        ax: float,
        ay: float,
        bx: float,
        by: float,
    ) -> float:
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            return hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        closest_x = ax + t * dx
        closest_y = ay + t * dy
        return hypot(px - closest_x, py - closest_y)
