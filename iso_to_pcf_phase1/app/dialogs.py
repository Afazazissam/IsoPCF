from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.dimension import DIMENSION_KINDS, DIRECTION_VALUES
from models.elbow import RADIUS_TYPES
from models.node import NODE_ROLES
from models.tee import TEE_TYPES


def optional_float(text: str) -> float | None:
    cleaned = text.strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def first_number(text: str) -> str:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return match.group(0) if match else ""


class FormDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.form = QFormLayout()
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addWidget(buttons)

    def line_edit(self, text: str = "", numeric: bool = False) -> QLineEdit:
        edit = QLineEdit(text)
        if numeric:
            validator = QDoubleValidator(edit)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            edit.setValidator(validator)
        return edit

    def notes_edit(self, text: str = "") -> QPlainTextEdit:
        edit = QPlainTextEdit(text)
        edit.setFixedHeight(72)
        return edit


class NodeDialog(FormDialog):
    def __init__(self, nearby_text: str, parent: QWidget | None = None) -> None:
        super().__init__("Add Node", parent)
        self.role = QComboBox()
        self.role.addItems(NODE_ROLES)
        self.nearby_text = self.notes_edit(nearby_text)
        self.notes = self.notes_edit()

        self.form.addRow("Node role", self.role)
        self.form.addRow("Nearby text", self.nearby_text)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, str]:
        return {
            "node_role": self.role.currentText(),
            "nearby_text": self.nearby_text.toPlainText().strip(),
            "notes": self.notes.toPlainText().strip(),
        }


class PipeSegmentDialog(FormDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Add Pipe Segment", parent)
        self.line_number = self.line_edit()
        self.nominal_diameter = self.line_edit(numeric=True)
        self.spec = self.line_edit()
        self.notes = self.notes_edit()

        self.form.addRow("Line number", self.line_number)
        self.form.addRow("Nominal diameter", self.nominal_diameter)
        self.form.addRow("Spec", self.spec)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        return {
            "line_number": self.line_number.text().strip(),
            "nominal_diameter": optional_float(self.nominal_diameter.text()),
            "spec": self.spec.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }


class ElbowDialog(FormDialog):
    def __init__(
        self,
        incoming_segment: str = "",
        outgoing_segment: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Add Elbow", parent)
        self.angle = self.line_edit("90", numeric=True)
        self.radius_type = QComboBox()
        self.radius_type.addItems(RADIUS_TYPES)
        self.radius_value = self.line_edit(numeric=True)
        self.incoming_segment = self.line_edit(incoming_segment)
        self.outgoing_segment = self.line_edit(outgoing_segment)
        self.notes = self.notes_edit()

        self.form.addRow("Angle deg", self.angle)
        self.form.addRow("Radius type", self.radius_type)
        self.form.addRow("Radius value", self.radius_value)
        self.form.addRow("Incoming segment", self.incoming_segment)
        self.form.addRow("Outgoing segment", self.outgoing_segment)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        angle_deg = optional_float(self.angle.text())
        return {
            "angle_deg": angle_deg if angle_deg is not None else 90.0,
            "radius_type": self.radius_type.currentText(),
            "radius_value": optional_float(self.radius_value.text()),
            "incoming_segment": self.incoming_segment.text().strip(),
            "outgoing_segment": self.outgoing_segment.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }


class TeeDialog(FormDialog):
    def __init__(self, segment_ids: list[str], parent: QWidget | None = None) -> None:
        super().__init__("Add Tee", parent)
        defaults = segment_ids + ["", "", ""]
        self.run_in_segment = self.line_edit(defaults[0])
        self.run_out_segment = self.line_edit(defaults[1])
        self.branch_segment = self.line_edit(defaults[2])
        self.tee_type = QComboBox()
        self.tee_type.addItems(TEE_TYPES)
        self.notes = self.notes_edit()

        self.form.addRow("Run in segment", self.run_in_segment)
        self.form.addRow("Run out segment", self.run_out_segment)
        self.form.addRow("Branch segment", self.branch_segment)
        self.form.addRow("Tee type", self.tee_type)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        return {
            "run_in_segment": self.run_in_segment.text().strip(),
            "run_out_segment": self.run_out_segment.text().strip(),
            "branch_segment": self.branch_segment.text().strip(),
            "tee_type": self.tee_type.currentText(),
            "notes": self.notes.toPlainText().strip(),
        }


class SupportDialog(FormDialog):
    def __init__(
        self,
        host_segment: str,
        distance_from_candidates: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Add Support", parent)
        self.host_segment = QLabel(host_segment)
        self.support_type = self.line_edit("unknown")
        self.distance_from_node = QComboBox()
        self.distance_from_node.addItems(distance_from_candidates)
        self.distance_value = self.line_edit(numeric=True)
        self.distance_unit = self.line_edit("mm")
        self.notes = self.notes_edit()

        self.form.addRow("Host segment", self.host_segment)
        self.form.addRow("Support type", self.support_type)
        self.form.addRow("Distance from node", self.distance_from_node)
        self.form.addRow("Distance value", self.distance_value)
        self.form.addRow("Distance unit", self.distance_unit)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        return {
            "support_type": self.support_type.text().strip() or "unknown",
            "distance_from_node": self.distance_from_node.currentText(),
            "distance_value": optional_float(self.distance_value.text()),
            "distance_unit": self.distance_unit.text().strip() or "mm",
            "notes": self.notes.toPlainText().strip(),
        }


class DimensionDialog(FormDialog):
    def __init__(self, source_text: str, parent: QWidget | None = None) -> None:
        super().__init__("Add Dimension", parent)
        self.value = self.line_edit(first_number(source_text), numeric=True)
        self.unit = self.line_edit("mm")
        self.kind = QComboBox()
        self.kind.addItems(DIMENSION_KINDS)
        self.direction = QComboBox()
        self.direction.addItems(DIRECTION_VALUES)
        self.source_text = self.notes_edit(source_text)
        self.notes = self.notes_edit()

        self.form.addRow("Value", self.value)
        self.form.addRow("Unit", self.unit)
        self.form.addRow("Dimension kind", self.kind)
        self.form.addRow("3D direction", self.direction)
        self.form.addRow("Source text", self.source_text)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        return {
            "value": optional_float(self.value.text()),
            "unit": self.unit.text().strip() or "mm",
            "dimension_kind": self.kind.currentText(),
            "direction": self.direction.currentText(),
            "source_text": self.source_text.toPlainText().strip(),
            "notes": self.notes.toPlainText().strip(),
        }


class CoordinateTagDialog(FormDialog):
    def __init__(self, source_text: str, parent: QWidget | None = None) -> None:
        super().__init__("Add Coordinate/Elevation Text", parent)
        self.east = self.line_edit(numeric=True)
        self.north = self.line_edit(numeric=True)
        self.elevation = self.line_edit(first_number(source_text), numeric=True)
        self.source_text = self.notes_edit(source_text)
        self.unit = self.line_edit("mm")
        self.notes = self.notes_edit()

        coord_row = QHBoxLayout()
        coord_row.addWidget(QLabel("E"))
        coord_row.addWidget(self.east)
        coord_row.addWidget(QLabel("N"))
        coord_row.addWidget(self.north)
        coord_widget = QWidget()
        coord_widget.setLayout(coord_row)

        self.form.addRow("Coordinates", coord_widget)
        self.form.addRow("Elevation", self.elevation)
        self.form.addRow("Source text", self.source_text)
        self.form.addRow("Unit", self.unit)
        self.form.addRow("Notes", self.notes)

    def values(self) -> dict[str, object]:
        return {
            "east": optional_float(self.east.text()),
            "north": optional_float(self.north.text()),
            "elevation": optional_float(self.elevation.text()),
            "source_text": self.source_text.toPlainText().strip(),
            "unit": self.unit.text().strip() or "mm",
            "notes": self.notes.toPlainText().strip(),
        }
