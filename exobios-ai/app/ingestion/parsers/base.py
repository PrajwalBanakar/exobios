from abc import ABC, abstractmethod

from pydantic import BaseModel


class ParsedPage(BaseModel):
    page_number: int
    text: str


class ParsedDocument(BaseModel):
    pages: list[ParsedPage]


class DocumentParser(ABC):
    """Common interface every format-specific parser implements. Adding a new
    format means adding a new DocumentParser subclass and registering it in
    ParserRegistry — no existing parser code changes (open/closed)."""

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> ParsedDocument: ...
