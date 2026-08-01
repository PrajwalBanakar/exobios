"""
writes MetadataPayload objects into Qdrant. id and vector are pulled out
to the top level (what Qdrant actually needs for indexing/search), while
the full payload — including the nested copy of the vector inside
VectorRecord — is stored alongside for completeness/traceability.
"""

from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from config.settings import settings
from core.reporting import reporter
from schemas.metadata_payload_schema import MetadataPayload
from schemas.step_result import StepResult, StepStatus

_client = QdrantClient(url=settings.qdrant_url)

VECTOR_SIZE = 384  # some hf model's vector sze
BATCH_SIZE = 100


def _ensure_collection():
    existing = [c.name for c in _client.get_collections().collections]
    if settings.collection_name not in existing:
        _client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def store_metadata_payloads(metadata_payloads: List[MetadataPayload]) -> bool:
    _ensure_collection()

    points = [
        PointStruct(
            id=str(mp.id),
            vector=mp.payload.chunk_payload.vector_record.vector,
            payload=mp.payload.model_dump(),
        )
        for mp in metadata_payloads
    ]

    try:
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            _client.upsert(collection_name=settings.collection_name, points=batch)
    except Exception as e:
        reporter.report(StepResult(
            step_name="qdrant_upsert",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="qdrant_upsert",
        status=StepStatus.SUCCESS,
        data={"num_points_stored": len(points)},
    ))
    return True