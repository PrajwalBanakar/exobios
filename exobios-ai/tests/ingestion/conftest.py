import io
from collections.abc import Callable

import fitz
import pytest
from docx import Document as DocxDocument


@pytest.fixture
def pdf_bytes_factory() -> Callable[[list[str]], bytes]:
    def _make(pages_text: list[str]) -> bytes:
        document = fitz.open()
        for text in pages_text:
            page = document.new_page()
            page.insert_text((72, 72), text)
        data = document.tobytes()
        document.close()
        return data

    return _make


@pytest.fixture
def docx_bytes_factory() -> Callable[[list[str]], bytes]:
    def _make(paragraphs: list[str]) -> bytes:
        document = DocxDocument()
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    return _make
