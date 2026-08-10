import re
from uuid import UUID

from app.ingestion.models.document import Subject
from app.ingestion.textbook.models import (
    ContentBlock,
    HeadingLevel,
    PageClassification,
    StructureState,
    TextbookChunk,
    TextbookChunkMetadata,
)
from app.ingestion.textbook.noise_filter import is_noise_text
from app.ingestion.textbook.structure_detector import StructureTracker
from app.prompting.builders.rag_prompt_builder import count_tokens

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# The context prefix (Step 20) is computed and prepended *after* a chunk's
# body is finalized, so its token cost isn't visible to the budgeting
# decisions below unless accounted for separately. Reserving a fixed
# headroom here — rather than the exact prefix length, which isn't known
# until finalize() builds it — keeps `oversized_chunks` in the summary a
# meaningful signal (genuine outliers) instead of firing on nearly every
# max-budget split purely from prefix overhead. 30 tokens comfortably
# covers "Chapter 99: <long title> > <section> > <subsection>".
_PREFIX_HEADROOM_TOKENS = 30


def _split_oversized_text(text: str, max_tokens: int) -> list[str]:
    """Last-resort splitter for a single block that alone exceeds
    max_tokens (an unusually large paragraph or table). Splits on sentence
    boundaries first; only hard-cuts by character count if a single
    "sentence" (no punctuation to split on) is still oversized."""
    sentences = _SENTENCE_SPLIT_RE.split(text)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and count_tokens(candidate) > max_tokens:
            pieces.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        pieces.append(current)

    final: list[str] = []
    char_budget = max_tokens * 4
    for piece in pieces:
        if count_tokens(piece) <= max_tokens:
            final.append(piece)
        else:
            final.extend(piece[i : i + char_budget] for i in range(0, len(piece), char_budget))
    return final


def _tail_overlap(text: str, overlap_tokens: int) -> str:
    if overlap_tokens <= 0:
        return ""
    overlap_chars = overlap_tokens * 4
    if len(text) <= overlap_chars:
        return text
    tail = text[-overlap_chars:]
    space_index = tail.find(" ")
    return tail[space_index + 1 :] if space_index != -1 else tail


def _context_prefix(state: StructureState) -> str:
    """A short, once-per-chunk orienting line (Step 20) so a chunk retrieved
    independently still carries its structural context, without repeating
    the full metadata into every paragraph."""
    parts: list[str] = []
    if state.chapter_number or state.chapter_title:
        label = f"Chapter {state.chapter_number}" if state.chapter_number else "Chapter"
        if state.chapter_title:
            label += f": {state.chapter_title}"
        parts.append(label)
    if state.section_title:
        parts.append(state.section_title)
    if state.subsection_title:
        parts.append(state.subsection_title)
    return " > ".join(parts)


class _Buffer:
    __slots__ = (
        "pieces",
        "start_page",
        "end_page",
        "start_printed",
        "end_printed",
        "classification",
        "figure_refs",
        "structure_snapshot",
    )

    def __init__(self) -> None:
        self.pieces: list[str] = []
        self.start_page: int | None = None
        self.end_page: int | None = None
        self.start_printed: int | None = None
        self.end_printed: int | None = None
        self.classification: PageClassification | None = None
        self.figure_refs: list[str] = []
        self.structure_snapshot: StructureState | None = None

    @property
    def is_empty(self) -> bool:
        return not self.pieces

    @property
    def token_count(self) -> int:
        return count_tokens("\n\n".join(self.pieces)) if self.pieces else 0

    def add(self, block: ContentBlock) -> None:
        if self.start_page is None:
            self.start_page = block.pdf_page_number
            self.start_printed = block.printed_page_number
            self.classification = block.page_classification
        self.end_page = block.pdf_page_number
        if block.printed_page_number is not None:
            self.end_printed = block.printed_page_number
        if block.is_figure_caption:
            self.figure_refs.append(block.text.strip())
        self.pieces.append(block.text)


class TextbookChunker:
    """Structure-aware, token-budgeted chunker for a whole document's
    ContentBlock stream. Boundary preference, in order: chapter/unit
    (always split — a chunk never crosses a chapter), section/subsection
    (split only once the target token budget is already reached), paragraph
    (a forced split at the max token ceiling never occurs mid-block), and
    finally sentence/character splitting only for a single block that alone
    exceeds the max ceiling.
    """

    def __init__(
        self,
        target_tokens: int,
        max_tokens: int,
        overlap_tokens: int,
        min_useful_tokens: int,
    ) -> None:
        if target_tokens <= 0 or max_tokens <= 0:
            raise ValueError("target_tokens and max_tokens must be positive")
        if max_tokens < target_tokens:
            raise ValueError("max_tokens must be >= target_tokens")
        if overlap_tokens < 0 or overlap_tokens >= target_tokens:
            raise ValueError("overlap_tokens must be non-negative and smaller than target_tokens")
        self._target_tokens = target_tokens
        self._max_tokens = max_tokens
        self._overlap_tokens = overlap_tokens
        self._min_useful_tokens = min_useful_tokens
        # Never let headroom reservation push the effective ceiling below
        # target_tokens — that would defeat "prefer accumulating to target"
        # for tightly-configured chunkers (e.g. in tests).
        self._effective_max_tokens = max(target_tokens, max_tokens - _PREFIX_HEADROOM_TOKENS)

    @property
    def target_tokens(self) -> int:
        return self._target_tokens

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def min_useful_tokens(self) -> int:
        return self._min_useful_tokens

    def chunk(
        self,
        document_id: UUID,
        subject: Subject | None,
        title: str | None,
        edition: str | None,
        blocks: list[ContentBlock],
    ) -> list[TextbookChunk]:
        tracker = StructureTracker()
        chunks: list[TextbookChunk] = []
        buffer = _Buffer()
        pending_overlap = ""
        chunk_index = 0

        def start_buffer(carry_overlap: str) -> _Buffer:
            fresh = _Buffer()
            if carry_overlap:
                fresh.pieces.append(carry_overlap)
            return fresh

        def finalize(buf: _Buffer) -> None:
            nonlocal chunk_index
            if buf.is_empty or buf.structure_snapshot is None:
                return
            body = "\n\n".join(buf.pieces)
            token_count = count_tokens(body)
            if is_noise_text(body, token_count, self._min_useful_tokens):
                return

            prefix = _context_prefix(buf.structure_snapshot)
            full_text = f"{prefix}\n\n{body}" if prefix else body

            metadata = TextbookChunkMetadata(
                document_id=document_id,
                subject=subject,
                title=title,
                edition=edition,
                unit_or_section=buf.structure_snapshot.unit_or_section,
                chapter_number=buf.structure_snapshot.chapter_number,
                chapter_title=buf.structure_snapshot.chapter_title,
                section_title=buf.structure_snapshot.section_title,
                subsection_title=buf.structure_snapshot.subsection_title,
                pdf_page_start=buf.start_page,
                pdf_page_end=buf.end_page,
                printed_page_start=buf.start_printed,
                printed_page_end=buf.end_printed,
                chunk_index=chunk_index,
                token_count=count_tokens(full_text),
                page_classification=buf.classification or PageClassification.UNKNOWN,
                figure_references=buf.figure_refs,
            )
            chunks.append(TextbookChunk(text=full_text, metadata=metadata))
            chunk_index += 1

        for block in blocks:
            if block.heading is not None:
                if block.heading.level in (HeadingLevel.CHAPTER, HeadingLevel.UNIT_SECTION):
                    finalize(buffer)
                    tracker.apply(block.heading)
                    buffer = start_buffer(
                        carry_overlap=""
                    )  # never carry overlap across a chapter/unit
                    buffer.structure_snapshot = tracker.state
                    buffer.add(block)
                    continue

                # HEADING / SUBHEADING: a soft boundary, only taken once
                # already at/over the target so short sections aren't
                # fragmented purely because a subheading appeared early.
                if buffer.token_count >= self._target_tokens:
                    pending_overlap = _tail_overlap(
                        "\n\n".join(buffer.pieces), self._overlap_tokens
                    )
                    finalize(buffer)
                    tracker.apply(block.heading)
                    buffer = start_buffer(carry_overlap=pending_overlap)
                    buffer.structure_snapshot = tracker.state
                    buffer.add(block)
                    continue

                tracker.apply(block.heading)
                # Buffer may already hold earlier content accumulated under
                # the *previous* structure state — only stamp the snapshot
                # when this heading is the buffer's first content, matching
                # _Buffer.add()'s own "first write wins" rule for start_page.
                if buffer.is_empty:
                    buffer.structure_snapshot = tracker.state
                buffer.add(block)
                continue

            # Body / table / caption content.
            block_tokens = count_tokens(block.text)
            if block_tokens > self._effective_max_tokens:
                # A single block alone exceeds the ceiling — flush whatever
                # is pending first, then emit the oversized block as its own
                # sentence-split run of chunks (never merged with neighbors).
                finalize(buffer)
                for piece in _split_oversized_text(block.text, self._effective_max_tokens):
                    sub_block = block.model_copy(update={"text": piece})
                    solo = _Buffer()
                    solo.structure_snapshot = tracker.state
                    solo.add(sub_block)
                    finalize(solo)
                buffer = start_buffer(carry_overlap="")
                buffer.structure_snapshot = tracker.state
                continue

            if (
                not buffer.is_empty
                and buffer.token_count + block_tokens > self._effective_max_tokens
            ):
                pending_overlap = _tail_overlap("\n\n".join(buffer.pieces), self._overlap_tokens)
                finalize(buffer)
                buffer = start_buffer(carry_overlap=pending_overlap)
                buffer.structure_snapshot = tracker.state

            if buffer.is_empty:
                buffer.structure_snapshot = tracker.state
            buffer.add(block)

        finalize(buffer)
        return chunks
