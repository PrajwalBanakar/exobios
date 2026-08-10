from collections.abc import Callable

import fitz
import pytest

Line = tuple[str, float, float, float]  # (text, fontsize, x, y)


@pytest.fixture
def pdf_builder() -> Callable[[list[list[Line]]], bytes]:
    """Builds a synthetic multi-page PDF from an explicit per-page list of
    (text, fontsize, x, y) lines — gives tests deterministic control over
    the font-size-relative heading detection, unlike a real book."""

    def _build(pages: list[list[Line]]) -> bytes:
        document = fitz.open()
        for page_spec in pages:
            page = document.new_page()
            for text, fontsize, x, y in page_spec:
                page.insert_text((x, y), text, fontsize=fontsize)
        content = document.tobytes()
        document.close()
        return content

    return _build


@pytest.fixture
def body_paragraph() -> Callable[[float, float, float], list[Line]]:
    """A multi-line body paragraph at 10pt, wrapped to fit page width,
    starting at (x, y)."""

    def _build(y: float, x: float = 72, fontsize: float = 10) -> list[Line]:
        text = (
            "The cardiac cycle refers to the sequence of mechanical and "
            "electrical events that repeat with every heartbeat. "
        ) * 6
        lines: list[Line] = []
        cursor_y = y
        for chunk in [text[i : i + 85] for i in range(0, len(text), 85)]:
            lines.append((chunk, fontsize, x, cursor_y))
            cursor_y += fontsize * 1.4
        return lines

    return _build
