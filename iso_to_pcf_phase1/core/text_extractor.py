from __future__ import annotations

from math import hypot

import fitz

from .pdf_document import PdfDocument


class TextExtractor:
    def nearby_text(
        self,
        document: PdfDocument,
        *,
        page_index: int,
        pdf_x: float,
        pdf_y: float,
        radius: float = 18.0,
    ) -> str:
        page = document.page(page_index)
        search_rect = fitz.Rect(pdf_x - radius, pdf_y - radius, pdf_x + radius, pdf_y + radius)
        words = page.get_text("words")
        nearby: list[tuple[float, float, str]] = []

        for word in words:
            x0, y0, x1, y1, text = word[:5]
            rect = fitz.Rect(x0, y0, x1, y1)
            center_x = (x0 + x1) / 2.0
            center_y = (y0 + y1) / 2.0
            if rect.intersects(search_rect) or hypot(center_x - pdf_x, center_y - pdf_y) <= radius:
                nearby.append((round(y0 / 4.0) * 4.0, x0, str(text)))

        nearby.sort(key=lambda item: (item[0], item[1]))
        return " ".join(item[2] for item in nearby).strip()
