from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.base import DocumentParser, ParsedDocument, ParsedPage


class TxtParser(DocumentParser):
    """Decodes plain text files as a single logical page."""

    _FORMAT_NAME = "TXT"

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="replace")

        if not text.strip():
            raise DocumentParseError(
                filename=filename, reason=f"{self._FORMAT_NAME} file is empty"
            )

        return ParsedDocument(pages=[ParsedPage(page_number=1, text=text)])
