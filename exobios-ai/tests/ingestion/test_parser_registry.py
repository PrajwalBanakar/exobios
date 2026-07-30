import pytest

from app.ingestion.exceptions import UnsupportedDocumentType
from app.ingestion.models.document import DocumentType
from app.ingestion.parsers.docx_parser import DocxParser
from app.ingestion.parsers.markdown_parser import MarkdownParser
from app.ingestion.parsers.pdf_parser import PdfParser
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.parsers.txt_parser import TxtParser


@pytest.mark.parametrize(
    ("document_type", "parser_type"),
    [
        (DocumentType.PDF, PdfParser),
        (DocumentType.DOCX, DocxParser),
        (DocumentType.TXT, TxtParser),
        (DocumentType.MARKDOWN, MarkdownParser),
    ],
)
def test_default_registry_resolves_built_in_parsers(document_type, parser_type):
    parser = ParserRegistry().get_parser(document_type)

    assert isinstance(parser, parser_type)


def test_register_parser_adds_new_format_without_touching_existing_ones():
    registry = ParserRegistry()

    class CustomParser(TxtParser):
        pass

    registry.register_parser(DocumentType.TXT, CustomParser())

    assert isinstance(registry.get_parser(DocumentType.TXT), CustomParser)
    assert isinstance(registry.get_parser(DocumentType.PDF), PdfParser)


def test_unregistered_type_raises_unsupported_document_type():
    registry = ParserRegistry(parsers={})

    with pytest.raises(UnsupportedDocumentType):
        registry.get_parser(DocumentType.PDF)
