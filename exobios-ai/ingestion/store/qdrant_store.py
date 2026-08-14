"""
writes MetadataPayload objects into Qdrant. id and vectors (dense and sparse)
are pulled out to the top level (what Qdrant actually needs for hybrid search),
while the full payload — including the nested copy of the vector inside
VectorRecord — is stored alongside for completeness/traceability.
"""

from typing import List

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from config.settings import settings
from core.reporting import reporter
from embedder.embedder import EMBED_MODEL_NAME
from schemas.metadata_payload_schema import MetadataPayload
from schemas.step_result import StepResult, StepStatus


_client = QdrantClient(url=settings.qdrant_url)

VECTOR_SIZE = 384  # some hf model's vector size
BATCH_SIZE = 100
_SPARSE_MODEL_NAME = "Qdrant/bm25"

_sparse_model = SparseTextEmbedding(model_name=_SPARSE_MODEL_NAME)

# Fixed, reserved point id for a single sentinel point per collection that
# carries corpus-level compatibility metadata (embedding model/dimension,
# sparse model) — Qdrant has no native collection-level custom-metadata
# field, so this is the standard workaround: one well-known, never-real-data
# point, distinct from real chunk ids (which are uuid5-derived from
# document_id:position — colliding with this exact value would require a
# hash collision). app/services/qdrant_service.py reads this point to
# detect ingestion/query embedding-config drift before trusting retrieval
# results. See the 2026-08 audit's Priority 6.
CORPUS_METADATA_POINT_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"


def _write_corpus_metadata():
    """Upserted on every ingestion run (idempotent — fixed id), not only on
    collection creation, so it self-heals if it's ever missing and always
    reflects the config this specific run actually used."""
    sparse = _get_sparse_vector("corpus metadata marker — not real content")
    _client.upsert(
        collection_name=settings.collection_name,
        points=[models.PointStruct(
            id=CORPUS_METADATA_POINT_ID,
            vector={"dense": [0.0] * VECTOR_SIZE, "sparse": sparse},
            payload={
                "_is_corpus_metadata": True,
                "embedding_model": EMBED_MODEL_NAME,
                "embedding_dimension": VECTOR_SIZE,
                "sparse_model": _SPARSE_MODEL_NAME,
                "ingestion_version": settings.ingestion_version,
            },
        )],
    )


def _ensure_collection():
    existing = [c.name for c in _client.get_collections().collections]
    if settings.collection_name not in existing:
        _client.create_collection(
            collection_name=settings.collection_name,
            vectors_config={
                "dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
            },
            sparse_vectors_config={
                # modifier=IDF is required for Qdrant to score BM25-style
                # sparse vectors with inverse-document-frequency weighting
                # server-side — without it, scoring degrades to raw term
                # frequency, and the sparse leg of the hybrid search app/'s
                # qdrant_service.hybrid_search() runs at query time is
                # weaker than intended.
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
            },
        )


def _get_sparse_vector(text: str) -> models.SparseVector:
    embedding = next(_sparse_model.embed([text]))
    return models.SparseVector(
        indices=embedding.indices.tolist(),
        values=embedding.values.tolist(),
    )


def store_metadata_payloads(metadata_payloads: List[MetadataPayload]) -> bool:
    _ensure_collection()
    try:
        _write_corpus_metadata()
    except Exception as e:
        # Non-fatal: the compatibility guard degrading to "unknown" on the
        # query side (see qdrant_service.py) is far better than blocking
        # real chunk storage over a metadata-point write failure.
        reporter.report(StepResult(step_name="write_corpus_metadata", status=StepStatus.FAIL, error_message=str(e)))

    points = []
    for mp in metadata_payloads:
        text_content = mp.payload.chunk_payload.chunk_metadata.content

        points.append(
            models.PointStruct(
                id=str(mp.id),
                vector={
                    "dense": mp.payload.chunk_payload.vector_record.vector,
                    "sparse": _get_sparse_vector(text_content),
                },
                payload=mp.payload.model_dump(),
            )
        )

    try:
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            _client.upsert(collection_name=settings.collection_name, points=batch)
    except Exception as e:
        reporter.report(
            StepResult(
                step_name="qdrant_upsert",
                status=StepStatus.FAIL,
                error_message=str(e),
            )
        )
        return False

    reporter.report(
        StepResult(
            step_name="qdrant_upsert",
            status=StepStatus.SUCCESS,
            data={"num_points_stored": len(points)},
        )
    )
    return True