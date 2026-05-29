from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from models.project import Project


COLLECTIONS = [
    ("nodes", "Nodes"),
    ("pipe_segments", "Pipe Segments"),
    ("elbows", "Elbows"),
    ("tees", "Tees"),
    ("supports", "Supports"),
    ("dimensions", "Dimensions"),
    ("coordinate_tags", "Coordinate Tags"),
]


class EntityPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: Project | None = None

        self.summary = QLabel("No project loaded")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Type", "Details"])
        self.tree.setAlternatingRowColors(True)
        self.tree.itemSelectionChanged.connect(self._show_current_item)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select an entity to inspect its JSON fields.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.summary)
        layout.addWidget(self.tree, stretch=3)
        layout.addWidget(self.details, stretch=2)

    def set_project(self, project: Project | None) -> None:
        self.project = project
        self.populate()

    def populate(self) -> None:
        self.tree.clear()
        self.details.clear()

        if self.project is None:
            self.summary.setText("No project loaded")
            return

        total = 0
        for collection_name, title in COLLECTIONS:
            items = list(getattr(self.project, collection_name))
            total += len(items)
            root = QTreeWidgetItem([f"{title} ({len(items)})", "", ""])
            root.setFirstColumnSpanned(True)
            root.setData(0, Qt.ItemDataRole.UserRole, None)
            self.tree.addTopLevelItem(root)

            for entity in items:
                row = QTreeWidgetItem(
                    [
                        getattr(entity, "id", ""),
                        getattr(entity, "type", ""),
                        self._entity_summary(entity),
                    ]
                )
                row.setData(0, Qt.ItemDataRole.UserRole, (collection_name, entity.id))
                root.addChild(row)
            root.setExpanded(True)

        self.summary.setText(f"{self.project.project_name} - {total} entities")
        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

    def select_entity(self, collection_name: str, entity_id: str) -> None:
        for root_index in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(root_index)
            for child_index in range(root.childCount()):
                item = root.child(child_index)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data == (collection_name, entity_id):
                    self.tree.setCurrentItem(item)
                    return

    def _show_current_item(self) -> None:
        if self.project is None:
            return
        items = self.tree.selectedItems()
        if not items:
            self.details.clear()
            return
        data = items[0].data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.details.clear()
            return
        collection_name, entity_id = data
        entity = self._find_entity(collection_name, entity_id)
        if entity is None:
            self.details.clear()
            return
        self.details.setPlainText(json.dumps(entity.to_dict(), indent=2, ensure_ascii=False))

    def _find_entity(self, collection_name: str, entity_id: str) -> Any | None:
        if self.project is None:
            return None
        return next(
            (
                entity
                for entity in getattr(self.project, collection_name)
                if getattr(entity, "id", "") == entity_id
            ),
            None,
        )

    @staticmethod
    def _entity_summary(entity: Any) -> str:
        if hasattr(entity, "node_role"):
            return f"{entity.node_role} @ ({entity.pdf_x:.2f}, {entity.pdf_y:.2f})"
        if hasattr(entity, "from_node") and hasattr(entity, "to_node"):
            return f"{entity.from_node} -> {entity.to_node}"
        if hasattr(entity, "center_node"):
            return f"center {entity.center_node}"
        if hasattr(entity, "support_node"):
            return f"{entity.support_node} on {entity.host_segment}"
        if hasattr(entity, "value"):
            return f"{entity.value} {entity.unit}"
        if hasattr(entity, "attached_node"):
            return f"attached {entity.attached_node}"
        return ""
