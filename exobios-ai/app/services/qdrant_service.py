import logging

import httpx
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException

from config.settings import settings
from core.exceptions import EmbeddingCompatibilityError, RetrievalException
from core.retry import retry_with_backoff

logger = logging.getLogger("app.qdrant")

# Same sparse model used at ingestion time — must match, or sparse vectors
# won't be comparable (see ALGORITHM.md / ingestion pipeline for the
# ingestion-side counterpart of this).
_SPARSE_MODEL_NAME = "Qdrant/bm25"

# Must match ingestion/store/qdrant_store.py's CORPUS_METADATA_POINT_ID exactly.
_CORPUS_METADATA_POINT_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"


def _is_retryable(e: Exception) -> bool:
    # Connection-level failures only (Qdrant down/unreachable/slow) — not
    # malformed-filter or other client-error cases, which retrying won't fix.
    return isinstance(e, (ResponseHandlingException, httpx.ConnectError, httpx.TimeoutException, ConnectionError, TimeoutError))


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant.url, api_key=settings.qdrant.api_key)
        self.collection_name = settings.qdrant.collection_name
        self._sparse_model = SparseTextEmbedding(model_name=_SPARSE_MODEL_NAME)
        self._compatibility_checked = False
        self.compatibility_warning: str | None = None

    def verify_embedding_compatibility(self) -> None:
        """Raises EmbeddingCompatibilityError on a CONFIRMED mismatch between
        this service's configured embedding model/dimension and what the
        Qdrant corpus was actually ingested with (recorded in a sentinel
        point by ingestion/store/qdrant_store.py). Cached after the first
        call — the corpus config doesn't change while this process runs.

        A corpus with NO compatibility metadata (ingested before this guard
        existed) is deliberately NOT a hard failure: breaking a known-
        working legacy corpus on upgrade would be worse than the silent-
        drift gap this guard closes going forward. See the 2026-08 audit's
        Priority 6. Qdrant being unreachable here is also not raised as
        EmbeddingCompatibilityError — hybrid_search's own retry/error
        handling covers that; this only ever raises for a confirmed,
        semantically-real config mismatch.
        """
        if self._compatibility_checked:
            return
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name, ids=[_CORPUS_METADATA_POINT_ID], with_payload=True,
            )
        except Exception as e:  # noqa: BLE001 — best-effort check; hybrid_search's own retry/error handling covers real failures
            logger.warning(f"could not verify embedding compatibility (will retry next call): {e}")
            return

        if not points:
            self.compatibility_warning = (
                "corpus has no compatibility metadata (ingested before this guard existed) "
                "— cannot verify embedding model/dimension match"
            )
            logger.warning(self.compatibility_warning)
            self._compatibility_checked = True
            return

        payload = points[0].payload or {}
        expected_model, expected_dim = settings.embedding.embed_model, settings.embedding.vector_size
        actual_model, actual_dim = payload.get("embedding_model"), payload.get("embedding_dimension")

        mismatches = []
        if actual_model and actual_model != expected_model:
            mismatches.append(f"embedding model: corpus was ingested with {actual_model!r}, this service is configured for {expected_model!r}")
        if actual_dim and actual_dim != expected_dim:
            mismatches.append(f"embedding dimension: corpus is {actual_dim}-dim, this service is configured for {expected_dim}-dim")

        self._compatibility_checked = True
        if mismatches:
            raise EmbeddingCompatibilityError("; ".join(mismatches))

    def _sparse_vector(self, text: str) -> models.SparseVector:
        embedding = next(self._sparse_model.embed([text]))
        return models.SparseVector(indices=embedding.indices.tolist(), values=embedding.values.tolist())

    def hybrid_search(self, query_text: str, dense_vector: list[float], filters: dict, top_k: int) -> list[dict]:
        # Outside the try/except below on purpose: a confirmed mismatch must
        # surface as EmbeddingCompatibilityError (500), not get folded into
        # RetrievalException (502) like a transient upstream failure would.
        self.verify_embedding_compatibility()

        def _call():
            qdrant_filter = self._build_filter(filters)
            sparse_vector = self._sparse_vector(query_text)

            return self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(query=dense_vector, using="dense", limit=top_k * 2, filter=qdrant_filter),
                    models.Prefetch(query=sparse_vector, using="sparse", limit=top_k * 2, filter=qdrant_filter),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
            )

        try:
            results = retry_with_backoff(_call, is_retryable=_is_retryable, op_name="qdrant hybrid search")
            return [
                {
                    "chunk_id": str(p.id),
                    "text": p.payload.get("chunk_payload", {}).get("chunk_metadata", {}).get("content", ""),
                    "payload": p.payload,
                    "score": p.score,
                }
                for p in results.points
            ]
        except Exception as e:
            raise RetrievalException(f"qdrant hybrid search failed: {e}") from e

    @staticmethod
    def _build_filter(filters: dict) -> models.Filter:
        conditions = []
        for key, value in (filters or {}).items():
            if value is None:
                continue
            field = f"document_payload.{key}"
            if isinstance(value, list):
                conditions.append(models.FieldCondition(key=field, match=models.MatchAny(any=value)))
            else:
                conditions.append(models.FieldCondition(key=field, match=models.MatchValue(value=value)))

        # Always applied, not just when other filters are present: excludes
        # chunks whose document has been explicitly superseded (see
        # ingestion's document-versioning migration/loader.py). A chunk with
        # NO is_active field at all — the entire pre-versioning corpus —
        # still matches, since `must_not MatchValue(False)` is satisfied by
        # an absent field, not just an explicit `true`. Non-destructive: no
        # re-ingestion needed for this to take effect on existing data.
        must_not = [models.FieldCondition(key="document_payload.is_active", match=models.MatchValue(value=False))]

        return models.Filter(must=conditions or None, must_not=must_not)


qdrant_service = QdrantService()    