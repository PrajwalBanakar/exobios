from app.ingestion.parsers.txt_parser import TxtParser


class MarkdownParser(TxtParser):
    """Decodes markdown files as raw text, identical to TxtParser.

    Kept as a distinct type (rather than reusing TxtParser directly) so the
    parser registry can map DocumentType.MARKDOWN to its own class, and so
    markdown-specific behavior (e.g. heading-aware handling) can be added
    later without touching TxtParser.
    """

    _FORMAT_NAME = "Markdown"
