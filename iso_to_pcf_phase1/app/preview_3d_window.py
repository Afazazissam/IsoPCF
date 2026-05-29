from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

_MPL_CONFIG_DIR = Path(tempfile.gettempdir()) / "iso_to_pcf_matplotlib"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget


class Preview3DWindow(QMainWindow):
    def __init__(self, geometry: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.geometry = geometry
        self.setWindowTitle("3D Geometry Preview")
        self.resize(1000, 760)

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.warning_box = QPlainTextEdit()
        self.warning_box.setReadOnly(True)
        self.warning_box.setMaximumHeight(110)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.warning_box)
        self.setCentralWidget(central)

        self._plot_geometry()
        self._show_warnings()

    def _plot_geometry(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection="3d")
        ax.set_title("Reconstructed 3D Stick Model")
        ax.set_xlabel("East / West (X)")
        ax.set_ylabel("North / South (Y)")
        ax.set_zlabel("Elevation (Z)")

        nodes = self.geometry.get("nodes", {})
        if not nodes:
            ax.text2D(0.5, 0.5, "No solved 3D coordinates", transform=ax.transAxes, ha="center")
            self.canvas.draw_idle()
            return

        for segment in self.geometry.get("segments", []):
            start = nodes.get(segment.get("from", ""))
            end = nodes.get(segment.get("to", ""))
            if not start or not end:
                continue
            ax.plot(
                [start["x"], end["x"]],
                [start["y"], end["y"]],
                [start["z"], end["z"]],
                color="#1f77b4",
                linewidth=2.4,
            )

        for node_id, point in nodes.items():
            ax.scatter(point["x"], point["y"], point["z"], color="#222222", s=28)
            ax.text(point["x"], point["y"], point["z"], f" {node_id}", fontsize=8)

        for component in self.geometry.get("components", []):
            point = nodes.get(component.get("node", ""))
            if point:
                self._plot_component(ax, component, point)

        self._draw_reference_axes(ax)
        self._set_equal_scale(ax, list(nodes.values()))
        ax.grid(True)
        self.canvas.draw_idle()

    def _plot_component(self, ax, component: dict[str, Any], point: dict[str, float]) -> None:
        component_type = component.get("type", "component")
        marker_styles = {
            "support": ("^", "#f2a900", 85),
            "elbow": ("s", "#ff7f0e", 65),
            "tee": ("D", "#2ca02c", 70),
            "valve": ("o", "#d62728", 80),
            "flange": ("P", "#9467bd", 80),
            "instrument": ("X", "#17becf", 80),
        }
        marker, color, size = marker_styles.get(component_type, ("o", "#666666", 55))
        ax.scatter(point["x"], point["y"], point["z"], marker=marker, color=color, s=size)
        if component.get("id"):
            ax.text(point["x"], point["y"], point["z"], f" {component['id']}", fontsize=8, color=color)

    def _draw_reference_axes(self, ax) -> None:
        nodes = self.geometry.get("nodes", {})
        max_extent = self._max_extent(list(nodes.values()))
        axis_len = max(1.0, max_extent * 0.18)
        ax.quiver(0, 0, 0, axis_len, 0, 0, color="#d62728", arrow_length_ratio=0.12)
        ax.quiver(0, 0, 0, 0, axis_len, 0, color="#2ca02c", arrow_length_ratio=0.12)
        ax.quiver(0, 0, 0, 0, 0, axis_len, color="#1f77b4", arrow_length_ratio=0.12)
        ax.text(axis_len, 0, 0, "East", color="#d62728")
        ax.text(0, axis_len, 0, "North", color="#2ca02c")
        ax.text(0, 0, axis_len, "Elevation", color="#1f77b4")

    def _set_equal_scale(self, ax, points: list[dict[str, float]]) -> None:
        xs = [point["x"] for point in points]
        ys = [point["y"] for point in points]
        zs = [point["z"] for point in points]
        max_range = max(
            max(xs) - min(xs),
            max(ys) - min(ys),
            max(zs) - min(zs),
            1.0,
        )
        half_range = max_range / 2.0
        center_x = (max(xs) + min(xs)) / 2.0
        center_y = (max(ys) + min(ys)) / 2.0
        center_z = (max(zs) + min(zs)) / 2.0
        ax.set_xlim(center_x - half_range, center_x + half_range)
        ax.set_ylim(center_y - half_range, center_y + half_range)
        ax.set_zlim(center_z - half_range, center_z + half_range)

    def _show_warnings(self) -> None:
        warnings = self.geometry.get("warnings", [])
        if warnings:
            self.warning_box.setPlainText("\n".join(warnings))
            self.warning_box.show()
        else:
            self.warning_box.setPlainText("3D preview generated without warnings.")

    @staticmethod
    def _max_extent(points: list[dict[str, float]]) -> float:
        if not points:
            return 1.0
        return max(
            max(abs(point["x"]) for point in points),
            max(abs(point["y"]) for point in points),
            max(abs(point["z"]) for point in points),
            1.0,
        )
