from __future__ import annotations

import fitz
from PySide6.QtGui import QImage, QPixmap

from .pdf_document import PdfDocument


class PdfRenderer:
    def render_page(self, document: PdfDocument, page_index: int, zoom: float) -> QPixmap:
        page = document.page(page_index)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        ).copy()
        return QPixmap.fromImage(image)
