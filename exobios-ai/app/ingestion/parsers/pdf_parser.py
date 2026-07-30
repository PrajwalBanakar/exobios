import fitz

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.base import DocumentParser, ParsedDocument, ParsedPage


class PdfParser(DocumentParser):
    """Extracts text page by page using PyMuPDF, preserving page numbers."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            document = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise DocumentParseError(filename=filename, reason=str(exc)) from exc

        try:
            pages = [
                ParsedPage(page_number=index + 1, text=page.get_text())
                for index, page in enumerate(document)
            ]
        finally:
            document.close()

        if not pages:
            raise DocumentParseError(filename=filename, reason="PDF contains no pages")

        return ParsedDocument(pages=pages)
