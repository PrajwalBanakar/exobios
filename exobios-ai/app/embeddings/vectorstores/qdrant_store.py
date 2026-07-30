from uuid import UUID

from qdrant_client import QdrantClient, models

from app.embeddings.exceptions import VectorStoreError
from app.embeddings.models.embedding import EmbeddedChunk, VectorMatch
from app.embeddings.vectorstores.base import VectorStore
from app.ingestion.models.document import DocumentMetadata

_DOCUMENT_ID_KEY = "document_id"


class QdrantVectorStore(VectorStore):
    """Qdrant-backed VectorStore. All qdrant_client specifics (point/filter
    construction, collection config) are contained here; nothing outside
    this module imports qdrant_client."""

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        vector_size: int,
        distance: models.Distance = models.Distance.COSINE,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._vector_size = vector_size
        self._distance = distance

    def initialize(self) -> None:
        try:
            existing = {c.name for c in self._client.get_collections().collections}
            if self._collection_name not in existing:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=self._vector_size, distance=self._distance
                    ),
                )
        except Exception as exc:
            raise VectorStoreError(reason=str(exc)) from exc

    def upsert_chunks(
        self, document: DocumentMetadata, embedded_chunks: list[EmbeddedChunk]
    ) -> None:
        if not embedded_chunks:
            return

        points = [
            models.PointStruct(
                id=str(item.chunk.id),
                vector=item.vector.values,
                payload=self._build_payload(document, item),
            )
            for item in embedded_chunks
        ]
        try:
            self._client.upsert(collection_name=self._collection_name, points=points)
        except Exception as exc:
            raise VectorStoreError(reason=str(exc)) from exc

    def delete_document(self, document_id: UUID) -> None:
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=models.FilterSelector(filter=self._document_filter(document_id)),
            )
        except Exception as exc:
            raise VectorStoreError(reason=str(exc)) from exc

    def document_exists(self, document_id: UUID) -> bool:
        try:
            points, _ = self._client.scroll(
                collection_name=self._collection_name,
                scroll_filter=self._document_filter(document_id),
                limit=1,
            )
        except Exception as exc:
            raise VectorStoreError(reason=str(exc)) from exc
        return len(points) > 0

    def search(
        self, query_vector: list[float], top_k: int, min_score: float | None = None
    ) -> list[VectorMatch]:
        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=min_score,
                with_payload=True,
            )
        except Exception as exc:
            raise VectorStoreError(reason=str(exc)) from exc

        return [
            VectorMatch(id=str(point.id), score=point.score, payload=point.payload or {})
            for point in response.points
        ]

    def health(self) -> bool:
        try:
            self._client.get_collections()
        except Exception:
            return False
        return True

    def _document_filter(self, document_id: UUID) -> models.Filter:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key=_DOCUMENT_ID_KEY, match=models.MatchValue(value=str(document_id))
                )
            ]
        )

    def _build_payload(self, document: DocumentMetadata, item: EmbeddedChunk) -> dict:
        return {
            _DOCUMENT_ID_KEY: str(document.id),
            "chunk_id": str(item.chunk.id),
            # Chunk text lives only here — Qdrant is the sole place per-chunk
            # content is stored, so retrieval (AI-4) depends on it being in
            # the payload to return anything more than ids and scores.
            "text": item.chunk.text,
            "page_number": item.chunk.metadata.page_number,
            "start_offset": item.chunk.metadata.start_offset,
            "end_offset": item.chunk.metadata.end_offset,
            "section_title": item.chunk.metadata.section_title,
            "document_type": document.document_type.value,
            "filename": document.filename,
            "language": document.language,
            "tags": document.tags,
            "version": document.version,
            "source": document.source,
        }
