from __future__ import annotations

from typing import Any

from .dimension_solver_basic import BasicDimensionSolver


class Geometry3DBuilder:
    def __init__(self, project_data: Any) -> None:
        self.project_data = project_data

    def build(self) -> dict[str, Any]:
        solution = BasicDimensionSolver(self.project_data).solve()
        nodes = solution["coordinates"]
        warnings = list(solution["warnings"])

        segments = []
        for segment in self._segments():
            from_node = self._value(segment, "from_node", "from", default="")
            to_node = self._value(segment, "to_node", "to", default="")
            segments.append(
                {
                    "id": str(self._value(segment, "id", default="")),
                    "from": str(from_node),
                    "to": str(to_node),
                    "type": str(self._value(segment, "type", default="pipe")),
                }
            )

        components = []
        for support in self._items("supports"):
            components.append(
                {
                    "id": str(self._value(support, "id", default="")),
                    "type": "support",
                    "node": str(self._value(support, "support_node", "node", default="")),
                    "host_segment": str(self._value(support, "host_segment", default="")),
                }
            )

        for elbow in self._items("elbows"):
            components.append(
                {
                    "id": str(self._value(elbow, "id", default="")),
                    "type": "elbow",
                    "node": str(self._value(elbow, "center_node", "node", default="")),
                }
            )

        for tee in self._items("tees"):
            components.append(
                {
                    "id": str(self._value(tee, "id", default="")),
                    "type": "tee",
                    "node": str(self._value(tee, "center_node", "node", default="")),
                }
            )

        for node in self._items("nodes"):
            role = str(self._value(node, "node_role", default=""))
            if role in {"valve_center", "flange_center", "instrument_point"}:
                components.append(
                    {
                        "id": str(self._value(node, "id", default="")),
                        "type": role.replace("_center", "").replace("_point", ""),
                        "node": str(self._value(node, "id", default="")),
                    }
                )

        for component in components:
            node_id = component.get("node", "")
            if node_id and node_id not in nodes:
                warnings.append(
                    f"Component {component.get('id', '(unnamed component)')} has unresolved coordinates."
                )

        return {
            "nodes": nodes,
            "segments": segments,
            "components": components,
            "unresolved_nodes": solution["unresolved_nodes"],
            "warnings": self._unique(warnings),
        }

    def _items(self, name: str) -> list[Any]:
        if isinstance(self.project_data, dict):
            return list(self.project_data.get(name, []))
        return list(getattr(self.project_data, name, []))

    def _segments(self) -> list[Any]:
        if isinstance(self.project_data, dict):
            return list(self.project_data.get("pipe_segments", self.project_data.get("segments", [])))
        return list(getattr(self.project_data, "pipe_segments", []))

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
    def _unique(messages: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_messages: list[str] = []
        for message in messages:
            if message not in seen:
                unique_messages.append(message)
                seen.add(message)
        return unique_messages
