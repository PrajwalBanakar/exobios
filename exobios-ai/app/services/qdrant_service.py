from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding

from config.settings import settings
from core.exceptions import RetrievalException

# Same sparse model used at ingestion time — must match, or sparse vectors
# won't be comparable (see ALGORITHM.md / ingestion pipeline for the
# ingestion-side counterpart of this).
_SPARSE_MODEL_NAME = "Qdrant/bm25"


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant.url)
        self.collection_name = settings.qdrant.collection_name
        self._sparse_model = SparseTextEmbedding(model_name=_SPARSE_MODEL_NAME)

    def _sparse_vector(self, text: str) -> models.SparseVector:
        embedding = next(self._sparse_model.embed([text]))
        return models.SparseVector(indices=embedding.indices.tolist(), values=embedding.values.tolist())

    def hybrid_search(self, query_text: str, dense_vector: list[float], filters: dict, top_k: int) -> list[dict]:
        try:
            qdrant_filter = self._build_filter(filters)
            sparse_vector = self._sparse_vector(query_text)

            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(query=dense_vector, using="dense", limit=top_k * 2, filter=qdrant_filter),
                    models.Prefetch(query=sparse_vector, using="sparse", limit=top_k * 2, filter=qdrant_filter),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
            )
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
            raise RetrievalException(f"qdrant hybrid search failed: {e}")

    @staticmethod
    def _build_filter(filters: dict) -> models.Filter | None:
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if value is None:
                continue
            field = f"document_payload.{key}"
            if isinstance(value, list):
                conditions.append(models.FieldCondition(key=field, match=models.MatchAny(any=value)))
            else:
                conditions.append(models.FieldCondition(key=field, match=models.MatchValue(value=value)))
        return models.Filter(must=conditions) if conditions else None


qdrant_service = QdrantService()    