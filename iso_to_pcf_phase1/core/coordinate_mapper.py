from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, QSizeF


@dataclass
class CoordinateMapper:
    page_size_pdf: QSizeF
    rendered_size: QSizeF
    page_offset_widget: QPointF
    render_scale: float = 1.0
    page_rotation: int = 0

    def widget_to_rendered(self, widget_point: QPointF) -> QPointF:
        return QPointF(
            widget_point.x() - self.page_offset_widget.x(),
            widget_point.y() - self.page_offset_widget.y(),
        )

    def rendered_to_widget(self, rendered_point: QPointF) -> QPointF:
        return QPointF(
            rendered_point.x() + self.page_offset_widget.x(),
            rendered_point.y() + self.page_offset_widget.y(),
        )

    def rendered_to_pdf(self, rendered_point: QPointF) -> QPointF:
        x = rendered_point.x() / self.render_scale
        y = rendered_point.y() / self.render_scale
        rotation = self.page_rotation % 360
        width = self.page_size_pdf.width()
        height = self.page_size_pdf.height()

        if rotation == 90:
            return QPointF(y, height - x)
        if rotation == 180:
            return QPointF(width - x, height - y)
        if rotation == 270:
            return QPointF(width - y, x)
        return QPointF(x, y)

    def pdf_to_rendered(self, pdf_point: QPointF) -> QPointF:
        rotation = self.page_rotation % 360
        width = self.page_size_pdf.width()
        height = self.page_size_pdf.height()
        x = pdf_point.x()
        y = pdf_point.y()

        if rotation == 90:
            return QPointF((height - y) * self.render_scale, x * self.render_scale)
        if rotation == 180:
            return QPointF((width - x) * self.render_scale, (height - y) * self.render_scale)
        if rotation == 270:
            return QPointF(y * self.render_scale, (width - x) * self.render_scale)
        return QPointF(x * self.render_scale, y * self.render_scale)

    def widget_to_pdf(self, widget_point: QPointF) -> QPointF | None:
        rendered = self.widget_to_rendered(widget_point)
        if not self._rendered_point_on_page(rendered):
            return None
        return self.rendered_to_pdf(rendered)

    def pdf_to_widget(self, pdf_point: QPointF) -> QPointF:
        return self.rendered_to_widget(self.pdf_to_rendered(pdf_point))

    def pdf_to_engineering(self, pdf_point: QPointF) -> QPointF:
        """Phase 1 keeps engineering coordinates unresolved and stores PDF-native points."""
        return QPointF(pdf_point.x(), pdf_point.y())

    def engineering_to_pdf(self, engineering_point: QPointF) -> QPointF:
        """Future constraint solving can replace this identity mapping."""
        return QPointF(engineering_point.x(), engineering_point.y())

    def _rendered_point_on_page(self, rendered_point: QPointF) -> bool:
        return (
            0 <= rendered_point.x() <= self.rendered_size.width()
            and 0 <= rendered_point.y() <= self.rendered_size.height()
        )
