from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from app.tool_panel import TOOL_PAN
from core.coordinate_mapper import CoordinateMapper
from core.pdf_document import PdfDocument
from core.pdf_renderer import PdfRenderer
from core.reconstruction_manager import ReconstructionManager
from core.text_extractor import TextExtractor


class PdfViewer(QWidget):
    mouse_pdf_position_changed = Signal(int, float, float)
    pdf_clicked = Signal(int, float, float, str)
    page_changed = Signal(int, int)
    tool_menu_requested = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.document: PdfDocument | None = None
        self.manager: ReconstructionManager | None = None
        self.renderer = PdfRenderer()
        self.text_extractor = TextExtractor()

        self.current_tool = "Select"
        self.page_index = 0
        self.zoom = 1.0
        self._render_zoom = 1.0
        self._fit_mode = True
        self._pan = QPointF(0.0, 0.0)
        self._pixmap: QPixmap | None = None
        self._mapper: CoordinateMapper | None = None
        self._dragging_pan = False
        self._last_pan_position = QPointF()
        self._highlighted_nodes: set[str] = set()
        self._highlighted_segments: set[str] = set()

    def set_document(self, document: PdfDocument) -> None:
        self.document = document
        self.page_index = 0
        self._fit_mode = True
        self._pan = QPointF(0.0, 0.0)
        self.render_current_page()

    def clear_document(self) -> None:
        self.document = None
        self.page_index = 0
        self._pixmap = None
        self._mapper = None
        self._pan = QPointF(0.0, 0.0)
        self.update()

    def set_reconstruction_manager(self, manager: ReconstructionManager) -> None:
        self.manager = manager
        self.update()

    def set_tool(self, tool_name: str) -> None:
        self.current_tool = tool_name
        self.setCursor(Qt.CursorShape.OpenHandCursor if tool_name == TOOL_PAN else Qt.CursorShape.ArrowCursor)

    def set_highlights(
        self,
        node_ids: set[str] | None = None,
        segment_ids: set[str] | None = None,
    ) -> None:
        self._highlighted_nodes = node_ids or set()
        self._highlighted_segments = segment_ids or set()
        self.update()

    def current_page_number(self) -> int:
        return self.page_index + 1

    def pick_tolerance_pdf(self) -> float:
        return max(6.0, 12.0 / max(self._render_zoom, 0.1))

    def next_page(self) -> None:
        if self.document and self.page_index < self.document.page_count - 1:
            self.set_current_page(self.page_index + 1)

    def previous_page(self) -> None:
        if self.document and self.page_index > 0:
            self.set_current_page(self.page_index - 1)

    def set_current_page(self, page_index: int) -> None:
        if not self.document:
            return
        self.page_index = max(0, min(page_index, self.document.page_count - 1))
        self._pan = QPointF(0.0, 0.0) if self._fit_mode else self._pan
        self.render_current_page()

    def zoom_in(self) -> None:
        self._zoom_by(1.25, QPointF(self.width() / 2.0, self.height() / 2.0))

    def zoom_out(self) -> None:
        self._zoom_by(0.8, QPointF(self.width() / 2.0, self.height() / 2.0))

    def fit_page(self) -> None:
        self._fit_mode = True
        self._pan = QPointF(0.0, 0.0)
        self.render_current_page()

    def render_current_page(self) -> None:
        if not self.document or not self.document.is_open:
            self._pixmap = None
            self._mapper = None
            self.update()
            return

        self._render_zoom = self._effective_zoom()
        self.zoom = self._render_zoom
        self._pixmap = self.renderer.render_page(self.document, self.page_index, self._render_zoom)
        self._update_mapper()
        self.page_changed.emit(self.page_index + 1, self.document.page_count)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#23272e"))

        if not self._pixmap or self._pixmap.isNull():
            self._draw_empty_state(painter)
            return

        offset = self._page_offset()
        painter.drawPixmap(offset, self._pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._draw_overlays(painter)

    def resizeEvent(self, event) -> None:  # noqa: N802
        if self._fit_mode:
            self.render_current_page()
        else:
            self._update_mapper()
            self.update()
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.document or not self._mapper:
            return

        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and self.current_tool == TOOL_PAN
        ):
            self._dragging_pan = True
            self._last_pan_position = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        pdf_point = self._mapper.widget_to_pdf(event.position())
        if pdf_point is None:
            return
        nearby_text = self._extract_nearby_text(pdf_point)
        self.pdf_clicked.emit(
            self.page_index + 1,
            float(pdf_point.x()),
            float(pdf_point.y()),
            nearby_text,
        )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging_pan:
            delta = event.position() - self._last_pan_position
            self._pan += delta
            self._last_pan_position = event.position()
            self._update_mapper()
            self.update()
            return

        if self._mapper:
            pdf_point = self._mapper.widget_to_pdf(event.position())
            if pdf_point is not None:
                self.mouse_pdf_position_changed.emit(
                    self.page_index + 1,
                    float(pdf_point.x()),
                    float(pdf_point.y()),
                )

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() in {
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.MiddleButton,
        }:
            self._dragging_pan = False
            self.set_tool(self.current_tool)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self.tool_menu_requested.emit(event.globalPos())
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if not self.document:
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom_by(factor, event.position())

    def _zoom_by(self, factor: float, anchor: QPointF) -> None:
        if not self.document:
            return

        old_pdf_point = self._mapper.widget_to_pdf(anchor) if self._mapper else None
        self._fit_mode = False
        self.zoom = max(0.1, min(8.0, self._render_zoom * factor))
        self.render_current_page()

        if old_pdf_point is not None and self._mapper is not None:
            new_anchor = self._mapper.pdf_to_widget(old_pdf_point)
            self._pan += anchor - new_anchor
            self._update_mapper()
            self.update()

    def _effective_zoom(self) -> float:
        if not self.document:
            return self.zoom
        if not self._fit_mode:
            return self.zoom

        page = self.document.page(self.page_index)
        available_width = max(1.0, self.width() - 48.0)
        available_height = max(1.0, self.height() - 48.0)
        width_zoom = available_width / max(1.0, float(page.rect.width))
        height_zoom = available_height / max(1.0, float(page.rect.height))
        return max(0.1, min(width_zoom, height_zoom))

    def _page_offset(self) -> QPointF:
        if not self._pixmap:
            return QPointF(0.0, 0.0)
        x = (self.width() - self._pixmap.width()) / 2.0 + self._pan.x()
        y = (self.height() - self._pixmap.height()) / 2.0 + self._pan.y()
        return QPointF(x, y)

    def _update_mapper(self) -> None:
        if not self.document or not self._pixmap:
            self._mapper = None
            return
        page = self.document.page(self.page_index)
        self._mapper = CoordinateMapper(
            page_size_pdf=QSizeF(float(page.rect.width), float(page.rect.height)),
            rendered_size=QSizeF(float(self._pixmap.width()), float(self._pixmap.height())),
            page_offset_widget=self._page_offset(),
            render_scale=self._render_zoom,
            page_rotation=int(page.rotation),
        )

    def _extract_nearby_text(self, pdf_point: QPointF) -> str:
        if not self.document:
            return ""
        try:
            return self.text_extractor.nearby_text(
                self.document,
                page_index=self.page_index,
                pdf_x=float(pdf_point.x()),
                pdf_y=float(pdf_point.y()),
            )
        except Exception:
            return ""

    def _draw_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QColor("#d2d7df"))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Open a PDF to begin reconstruction")

    def _draw_overlays(self, painter: QPainter) -> None:
        if not self.manager or not self._mapper:
            return

        project = self.manager.project
        page_number = self.page_index + 1
        node_by_id = {node.id: node for node in project.nodes}

        painter.setFont(QFont("Segoe UI", 8))

        for segment in project.pipe_segments:
            if segment.page_number != page_number:
                continue
            start = node_by_id.get(segment.from_node)
            end = node_by_id.get(segment.to_node)
            if not start or not end:
                continue
            start_point = self._mapper.pdf_to_widget(QPointF(start.pdf_x, start.pdf_y))
            end_point = self._mapper.pdf_to_widget(QPointF(end.pdf_x, end.pdf_y))
            color = QColor("#f3c846") if segment.id in self._highlighted_segments else QColor("#4ca3dd")
            painter.setPen(QPen(color, 2.4 if segment.id in self._highlighted_segments else 1.8))
            painter.drawLine(start_point, end_point)
            self._draw_label(painter, self._midpoint(start_point, end_point), segment.id, color)

        for dimension in project.dimensions:
            if dimension.page_number != page_number:
                continue
            start = node_by_id.get(dimension.from_node)
            end = node_by_id.get(dimension.to_node)
            if not start or not end:
                continue
            start_point = self._mapper.pdf_to_widget(QPointF(start.pdf_x, start.pdf_y))
            end_point = self._mapper.pdf_to_widget(QPointF(end.pdf_x, end.pdf_y))
            pen = QPen(QColor("#b574ff"), 1.4)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(start_point, end_point)
            label = f"{dimension.id}"
            if dimension.value is not None:
                label = f"{dimension.id}: {dimension.value:g} {dimension.unit}"
            self._draw_label(
                painter,
                self._midpoint(start_point, end_point) + QPointF(0, -12),
                label,
                QColor("#d3b5ff"),
            )

        for elbow in project.elbows:
            node = node_by_id.get(elbow.center_node)
            if not node or node.page_number != page_number:
                continue
            point = self._mapper.pdf_to_widget(QPointF(node.pdf_x, node.pdf_y))
            painter.setPen(QPen(QColor("#ff8f4f"), 1.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(point, 11, 11)
            painter.drawLine(point + QPointF(-8, 0), point + QPointF(8, 0))
            painter.drawLine(point + QPointF(0, -8), point + QPointF(0, 8))

        for tee in project.tees:
            node = node_by_id.get(tee.center_node)
            if not node or node.page_number != page_number:
                continue
            point = self._mapper.pdf_to_widget(QPointF(node.pdf_x, node.pdf_y))
            painter.setPen(QPen(QColor("#74d68c"), 1.8))
            painter.setBrush(QColor(116, 214, 140, 70))
            painter.drawRect(QRectF(point.x() - 7, point.y() - 7, 14, 14))
            self._draw_label(painter, point + QPointF(8, -8), tee.id, QColor("#a5f0b6"))

        for support in project.supports:
            node = node_by_id.get(support.support_node)
            if not node or node.page_number != page_number:
                continue
            point = self._mapper.pdf_to_widget(QPointF(node.pdf_x, node.pdf_y))
            triangle = QPolygonF(
                [
                    point + QPointF(0, -9),
                    point + QPointF(-8, 8),
                    point + QPointF(8, 8),
                ]
            )
            painter.setPen(QPen(QColor("#fbda66"), 1.6))
            painter.setBrush(QColor(251, 218, 102, 95))
            painter.drawPolygon(triangle)
            self._draw_label(painter, point + QPointF(9, 8), support.id, QColor("#ffeaa0"))

        for tag in project.coordinate_tags:
            node = node_by_id.get(tag.attached_node)
            if not node or node.page_number != page_number:
                continue
            point = self._mapper.pdf_to_widget(QPointF(node.pdf_x, node.pdf_y))
            painter.setPen(QPen(QColor("#65e2d9"), 1.6))
            painter.setBrush(QColor(101, 226, 217, 80))
            painter.drawRoundedRect(QRectF(point.x() - 8, point.y() - 8, 16, 16), 2, 2)
            self._draw_label(painter, point + QPointF(10, -8), tag.id, QColor("#a5fff8"))

        for node in project.nodes:
            if node.page_number != page_number:
                continue
            point = self._mapper.pdf_to_widget(QPointF(node.pdf_x, node.pdf_y))
            highlighted = node.id in self._highlighted_nodes
            painter.setPen(QPen(QColor("#f3c846") if highlighted else QColor("#ffffff"), 1.6))
            painter.setBrush(QColor("#f3c846") if highlighted else QColor("#ff4f72"))
            radius = 6.5 if highlighted else 5.0
            painter.drawEllipse(point, radius, radius)
            self._draw_label(painter, point + QPointF(7, -7), node.id, QColor("#ffffff"))

    @staticmethod
    def _midpoint(first: QPointF, second: QPointF) -> QPointF:
        return QPointF((first.x() + second.x()) / 2.0, (first.y() + second.y()) / 2.0)

    @staticmethod
    def _draw_label(painter: QPainter, point: QPointF, text: str, color: QColor) -> None:
        painter.setPen(color)
        painter.drawText(point, text)
