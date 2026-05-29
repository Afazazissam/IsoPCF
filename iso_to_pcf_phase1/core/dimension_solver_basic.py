from __future__ import annotations

from math import dist
from typing import Any


Coordinate = tuple[float, float, float]


DIRECTION_VECTORS: dict[str, Coordinate] = {
    "EAST": (1.0, 0.0, 0.0),
    "WEST": (-1.0, 0.0, 0.0),
    "NORTH": (0.0, 1.0, 0.0),
    "SOUTH": (0.0, -1.0, 0.0),
    "UP": (0.0, 0.0, 1.0),
    "DOWN": (0.0, 0.0, -1.0),
}


class BasicDimensionSolver:
    """Phase 1B coordinate propagation from directional dimensions."""

    def __init__(self, project_data: Any) -> None:
        self.project_data = project_data

    def solve(self) -> dict[str, Any]:
        nodes = self._items("nodes")
        node_ids = [str(self._value(node, "id")) for node in nodes if self._value(node, "id")]
        warnings: list[str] = []

        if not node_ids:
            return {
                "coordinates": {},
                "unresolved_nodes": [],
                "warnings": ["No nodes are available for 3D preview."],
            }

        coordinates: dict[str, Coordinate] = {node_ids[0]: (0.0, 0.0, 0.0)}
        dimensions = self._items("dimensions")

        if not dimensions:
            warnings.append("No directional dimensions are available for 3D coordinate solving.")

        for _ in range(max(1, len(dimensions) + len(node_ids))):
            changed = False
            for dimension in dimensions:
                changed = self._try_apply_dimension(
                    dimension,
                    coordinates,
                    set(node_ids),
                    warnings,
                ) or changed
            if not changed:
                break

        unresolved_nodes = [node_id for node_id in node_ids if node_id not in coordinates]
        for node_id in unresolved_nodes:
            warnings.append(f"Node {node_id} has unresolved 3D coordinates.")

        for segment in self._segments():
            segment_id = str(self._value(segment, "id", default="(unnamed segment)"))
            from_node = self._segment_from(segment)
            to_node = self._segment_to(segment)
            if not from_node or not to_node:
                warnings.append(f"Segment {segment_id} is missing endpoint node references.")
            elif from_node not in node_ids or to_node not in node_ids:
                warnings.append(f"Segment {segment_id} references a missing node.")
            elif from_node not in coordinates or to_node not in coordinates:
                warnings.append(f"Segment {from_node}-{to_node} has unresolved coordinates.")

        return {
            "coordinates": {
                node_id: {"x": xyz[0], "y": xyz[1], "z": xyz[2]}
                for node_id, xyz in coordinates.items()
            },
            "unresolved_nodes": unresolved_nodes,
            "warnings": self._unique(warnings),
        }

    def _try_apply_dimension(
        self,
        dimension: Any,
        coordinates: dict[str, Coordinate],
        node_ids: set[str],
        warnings: list[str],
    ) -> bool:
        dimension_id = str(self._value(dimension, "id", default="(unnamed dimension)"))
        from_node = self._dimension_from(dimension)
        to_node = self._dimension_to(dimension)

        if not from_node or not to_node:
            warnings.append(f"Dimension {dimension_id} is missing endpoint node references.")
            return False
        if from_node not in node_ids or to_node not in node_ids:
            warnings.append(f"Dimension {dimension_id} references a missing node.")
            return False

        value = self._dimension_value(dimension)
        if value is None:
            warnings.append(f"Dimension {dimension_id} has no numeric value.")
            return False

        vector = self._dimension_vector(dimension)
        if vector is None:
            warnings.append(f"Dimension {dimension_id} has no usable 3D direction.")
            return False

        delta = (vector[0] * value, vector[1] * value, vector[2] * value)

        if from_node in coordinates and to_node not in coordinates:
            coordinates[to_node] = self._add(coordinates[from_node], delta)
            return True

        if to_node in coordinates and from_node not in coordinates:
            coordinates[from_node] = self._subtract(coordinates[to_node], delta)
            return True

        if from_node in coordinates and to_node in coordinates:
            expected_to = self._add(coordinates[from_node], delta)
            if dist(expected_to, coordinates[to_node]) > 1e-6:
                warnings.append(
                    f"Dimension {dimension_id} conflicts with already solved coordinates."
                )

        return False

    def _dimension_vector(self, dimension: Any) -> Coordinate | None:
        direction = str(self._value(dimension, "direction", default="")).strip().upper()
        if direction in {"ELEVATION", "ELEV"}:
            direction = "UP"
        if direction in DIRECTION_VECTORS:
            return DIRECTION_VECTORS[direction]

        kind = str(self._value(dimension, "dimension_kind", "kind", default="")).strip().lower()
        if kind == "east_west":
            return DIRECTION_VECTORS["EAST"]
        if kind == "north_south":
            return DIRECTION_VECTORS["NORTH"]
        if kind == "elevation":
            return DIRECTION_VECTORS["UP"]

        source_text = str(self._value(dimension, "source_text", default="")).upper()
        for candidate in ("EAST", "WEST", "NORTH", "SOUTH", "UP", "DOWN"):
            if candidate in source_text:
                return DIRECTION_VECTORS[candidate]
        return None

    def _dimension_value(self, dimension: Any) -> float | None:
        value = self._value(dimension, "value", default=None)
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _items(self, name: str) -> list[Any]:
        if isinstance(self.project_data, dict):
            return list(self.project_data.get(name, []))
        return list(getattr(self.project_data, name, []))

    def _segments(self) -> list[Any]:
        if isinstance(self.project_data, dict):
            return list(self.project_data.get("pipe_segments", self.project_data.get("segments", [])))
        return list(getattr(self.project_data, "pipe_segments", []))

    def _dimension_from(self, dimension: Any) -> str:
        return str(self._value(dimension, "from_node", "from", default=""))

    def _dimension_to(self, dimension: Any) -> str:
        return str(self._value(dimension, "to_node", "to", default=""))

    def _segment_from(self, segment: Any) -> str:
        return str(self._value(segment, "from_node", "from", default=""))

    def _segment_to(self, segment: Any) -> str:
        return str(self._value(segment, "to_node", "to", default=""))

    @staticmethod
    def _value(item: Any, *names: str, default: Any = "") -> Any:
        if isinstance(item, dict):
            for name in names:
                if name in item:
                    return item[name]
            return default

        for name in names:
            if hasattr(item, name):
                return getattr(item, name)
        return default

    @staticmethod
    def _add(first: Coordinate, second: Coordinate) -> Coordinate:
        return (first[0] + second[0], first[1] + second[1], first[2] + second[2])

    @staticmethod
    def _subtract(first: Coordinate, second: Coordinate) -> Coordinate:
        return (first[0] - second[0], first[1] - second[1], first[2] - second[2])

    @staticmethod
    def _unique(messages: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_messages: list[str] = []
        for message in messages:
            if message not in seen:
                unique_messages.append(message)
                seen.add(message)
        return unique_messages
