from __future__ import annotations

from pathlib import Path

import fitz

from models.project import PageInfo


class PdfDocument:
    def __init__(self) -> None:
        self.path: Path | None = None
        self._document: fitz.Document | None = None

    @property
    def is_open(self) -> bool:
        return self._document is not None

    @property
    def page_count(self) -> int:
        return len(self._document) if self._document else 0

    def open(self, path: str | Path) -> None:
        self.close()
        self.path = Path(path)
        self._document = fitz.open(str(self.path))

    def close(self) -> None:
        if self._document is not None:
            self._document.close()
        self.path = None
        self._document = None

    def page(self, page_index: int) -> fitz.Page:
        if self._document is None:
            raise RuntimeError("No PDF document is open.")
        return self._document.load_page(page_index)

    def page_infos(self) -> list[PageInfo]:
        return [
            PageInfo(
                page_number=index + 1,
                width=float(self.page(index).rect.width),
                height=float(self.page(index).rect.height),
                rotation=int(self.page(index).rotation),
            )
            for index in range(self.page_count)
        ]
