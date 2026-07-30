from uuid import UUID

from app.prompting.exceptions import ContextFormattingError
from app.prompting.models.prompt import CitedChunk, DocumentGroup, RetrievedContext
from app.retrieval.models.retrieval import RetrievedChunk


class ContextFormatter:
    """Turns a raw, possibly-duplicated, unordered list of RetrievedChunks
    into a RetrievedContext ready for prompt assembly: deduplicated, sorted
    by relevance with fully deterministic tie-breaking, numbered for
    citation, and grouped by source document.

    Runs independently of whatever produced the chunks (e.g. it doesn't
    assume RetrievalService's Reranker already deduplicated/sorted them),
    so it's correct and testable in isolation.
    """

    def format(self, chunks: list[RetrievedChunk]) -> RetrievedContext:
        try:
            deduped = self._deduplicate(chunks)
            ordered = self._sort_deterministically(deduped)
            cited = [
                CitedChunk(citation_number=number, chunk=chunk)
                for number, chunk in enumerate(ordered, start=1)
            ]
            groups = self._group_by_document(cited)
        except ContextFormattingError:
            raise
        except Exception as exc:
            raise ContextFormattingError(reason=str(exc)) from exc

        return RetrievedContext(groups=groups, total_chunks=len(cited))

    def _deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        best_by_chunk_id: dict[UUID, RetrievedChunk] = {}
        for chunk in chunks:
            existing = best_by_chunk_id.get(chunk.chunk_id)
            if existing is None or chunk.score > existing.score:
                best_by_chunk_id[chunk.chunk_id] = chunk
        return list(best_by_chunk_id.values())

    def _sort_deterministically(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        # Descending score is the primary key; everything after it exists
        # only to make ordering reproducible when scores tie.
        return sorted(
            chunks,
            key=lambda c: (
                -c.score,
                c.filename,
                c.page_number if c.page_number is not None else -1,
                str(c.chunk_id),
            ),
        )

    def _group_by_document(self, cited_chunks: list[CitedChunk]) -> list[DocumentGroup]:
        groups: dict[UUID, DocumentGroup] = {}
        order: list[UUID] = []
        for cited in cited_chunks:
            chunk = cited.chunk
            if chunk.document_id not in groups:
                groups[chunk.document_id] = DocumentGroup(
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    document_type=chunk.document_type,
                    source=chunk.source,
                    citations=[],
                )
                order.append(chunk.document_id)
            groups[chunk.document_id].citations.append(cited)
        return [groups[document_id] for document_id in order]
