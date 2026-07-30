import re
from collections import Counter

from app.ingestion.parsers.base import ParsedPage

_INLINE_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")


class TextCleaner:
    """Normalizes extracted text without touching word content.

    Only horizontal whitespace and blank-line runs are collapsed, so bullet
    markers ("-", "*"), numbering ("1.", "a)"), and medical terminology
    (abbreviations, units, punctuation inside words) are left untouched.
    Repeated header/footer lines are detected across pages and stripped.
    """

    def __init__(
        self,
        header_footer_min_page_ratio: float = 0.6,
        min_pages_for_header_footer_detection: int = 3,
    ) -> None:
        self._header_footer_min_page_ratio = header_footer_min_page_ratio
        self._min_pages = min_pages_for_header_footer_detection

    def clean_pages(self, pages: list[ParsedPage]) -> list[ParsedPage]:
        normalized = [
            ParsedPage(page_number=page.page_number, text=self._normalize_whitespace(page.text))
            for page in pages
        ]
        return self._strip_repeated_headers_footers(normalized)

    def _normalize_whitespace(self, text: str) -> str:
        lines = [_INLINE_WHITESPACE_RE.sub(" ", line).rstrip() for line in text.splitlines()]
        collapsed = _MULTI_BLANK_LINE_RE.sub("\n\n", "\n".join(lines))
        return collapsed.strip("\n")

    def _strip_repeated_headers_footers(self, pages: list[ParsedPage]) -> list[ParsedPage]:
        if len(pages) < self._min_pages:
            return pages

        first_lines: Counter[str] = Counter()
        last_lines: Counter[str] = Counter()
        for page in pages:
            lines = [line for line in page.text.splitlines() if line.strip()]
            if not lines:
                continue
            first_lines[lines[0]] += 1
            last_lines[lines[-1]] += 1

        threshold = max(2, int(len(pages) * self._header_footer_min_page_ratio))
        repeated_headers = {line for line, count in first_lines.items() if count >= threshold}
        repeated_footers = {line for line, count in last_lines.items() if count >= threshold}
        if not repeated_headers and not repeated_footers:
            return pages

        cleaned = []
        for page in pages:
            lines = page.text.splitlines()
            if lines and lines[0] in repeated_headers:
                lines = lines[1:]
            if lines and lines[-1] in repeated_footers:
                lines = lines[:-1]
            cleaned.append(
                ParsedPage(page_number=page.page_number, text="\n".join(lines).strip("\n"))
            )
        return cleaned
