from app.ingestion.exceptions import UnsupportedDocumentType
from app.ingestion.models.document import DocumentType
from app.ingestion.parsers.base import DocumentParser
from app.ingestion.parsers.docx_parser import DocxParser
from app.ingestion.parsers.markdown_parser import MarkdownParser
from app.ingestion.parsers.pdf_parser import PdfParser
from app.ingestion.parsers.txt_parser import TxtParser


class ParserRegistry:
    """Maps a DocumentType to the parser that handles it.

    New formats are added by calling register_parser — existing parsers and
    callers are untouched (open/closed).
    """

    def __init__(self, parsers: dict[DocumentType, DocumentParser] | None = None) -> None:
        self._parsers: dict[DocumentType, DocumentParser] = (
            parsers
            if parsers is not None
            else {
                DocumentType.PDF: PdfParser(),
                DocumentType.DOCX: DocxParser(),
                DocumentType.TXT: TxtParser(),
                DocumentType.MARKDOWN: MarkdownParser(),
            }
        )

    def get_parser(self, document_type: DocumentType) -> DocumentParser:
        parser = self._parsers.get(document_type)
        if parser is None:
            raise UnsupportedDocumentType(filename=str(document_type))
        return parser

    def register_parser(self, document_type: DocumentType, parser: DocumentParser) -> None:
        self._parsers[document_type] = parser
