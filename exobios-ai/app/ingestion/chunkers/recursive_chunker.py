import re
from uuid import UUID

from app.ingestion.chunkers.base import Chunker
from app.ingestion.exceptions import ChunkingError
from app.ingestion.models.chunk import Chunk, ChunkMetadata
from app.ingestion.parsers.base import ParsedPage

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

_MD_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$")
_NUMBERED_HEADING_RE = re.compile(r"^\d{1,2}(\.\d+)*[.)]\s+[A-Z][^.]{2,78}$")
_MAX_HEADING_LOOKBACK_LINES = 300


def _looks_like_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 80:
        return None
    md_match = _MD_HEADING_RE.match(stripped)
    if md_match:
        return md_match.group(1).strip()
    if _NUMBERED_HEADING_RE.match(stripped):
        return stripped
    if stripped.isupper() and len(stripped) >= 3 and not stripped.endswith((".", ",", ";")):
        return stripped
    return None


def _detect_section_title(text: str, offset: int) -> str | None:
    preceding_lines = text[:offset].splitlines()
    for line in reversed(preceding_lines[-_MAX_HEADING_LOOKBACK_LINES:]):
        heading = _looks_like_heading(line)
        if heading:
            return heading
    return None


class RecursiveChunker(Chunker):
    """Splits page text into overlapping chunks.

    Text is first partitioned (with no overlap) by recursively trying each
    separator in `separators`, in order, only descending to the next
    separator for pieces still larger than chunk_size — this keeps splits on
    natural boundaries (paragraph, then line, then sentence, then word)
    whenever possible. Overlap is then applied as a sliding window over the
    partition boundaries, so offsets always point into the original
    (cleaned) page text.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: list[str] | None = None,
    ) -> None:
        if chunk_size <= 0:
            raise ChunkingError(reason="chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ChunkingError(
                reason="chunk_overlap must be non-negative and smaller than chunk_size"
            )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or DEFAULT_SEPARATORS

    def chunk(self, document_id: UUID, pages: list[ParsedPage]) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_number = 0
        for page in pages:
            if not page.text.strip():
                continue
            for start, end in self._split_with_offsets(page.text):
                chunk_number += 1
                chunks.append(
                    Chunk(
                        text=page.text[start:end],
                        metadata=ChunkMetadata(
                            document_id=document_id,
                            page_number=page.page_number,
                            chunk_number=chunk_number,
                            start_offset=start,
                            end_offset=end,
                            section_title=_detect_section_title(page.text, start),
                        ),
                    )
                )

        if not chunks:
            raise ChunkingError(
                reason="No chunks were produced from the document", document_id=document_id
            )

        return chunks

    def _split_with_offsets(self, text: str) -> list[tuple[int, int]]:
        pieces = self._split_text(text, self._separators)

        spans: list[tuple[int, int]] = []
        cursor = 0
        for piece in pieces:
            start, end = cursor, cursor + len(piece)
            spans.append((start, end))
            cursor = end

        if self._chunk_overlap == 0 or len(spans) <= 1:
            return spans

        overlapped = [spans[0]]
        for i in range(1, len(spans)):
            start, end = spans[i]
            prev_start = spans[i - 1][0]
            new_start = max(start - self._chunk_overlap, prev_start)
            overlapped.append((new_start, end))
        return overlapped

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        """Partitions `text` into pieces <= chunk_size. Concatenating the
        returned pieces in order always reconstructs `text` exactly, which is
        what lets `_split_with_offsets` compute offsets with a running cursor
        instead of re-searching the text.
        """
        if len(text) <= self._chunk_size:
            return [text] if text else []

        separator = separators[0] if separators else ""
        remaining_separators = separators[1:]
        parts = list(text) if separator == "" else text.split(separator)

        merged: list[str] = []
        current = ""
        for index, part in enumerate(parts):
            piece = part + separator if separator and index < len(parts) - 1 else part
            candidate = current + piece
            if len(candidate) <= self._chunk_size:
                current = candidate
                continue

            if current:
                merged.append(current)
                current = ""

            if len(piece) > self._chunk_size:
                if remaining_separators:
                    merged.extend(self._split_text(piece, remaining_separators))
                else:
                    merged.append(piece)
            else:
                current = piece

        if current:
            merged.append(current)
        return merged
