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
from schemas.metadata_payload_schema import MetadataPayload
from schemas.step_result import StepResult, StepStatus

_client = QdrantClient(url=settings.qdrant_url)

VECTOR_SIZE = 384  # some hf model's vector size
BATCH_SIZE = 100
_SPARSE_MODEL_NAME = "Qdrant/bm25"

# Initialize sparse embedding model lazily or globally
_sparse_model = SparseTextEmbedding(model_name=_SPARSE_MODEL_NAME)


def _ensure_collection():
    existing = [c.name for c in _client.get_collections().collections]
    if settings.collection_name not in existing:
        _client.create_collection(
            collection_name=settings.collection_name,
            vectors_config={
                "dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(),
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

    points = []
    for mp in metadata_payloads:
        text_content = mp.payload.chunk_payload.text_content

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