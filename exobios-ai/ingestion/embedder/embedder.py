"""
input: stream of chunks + tokens in batches
output: vector embedding for every chunk 
also build the chunk meta data here


"""


"""
for a list of ChunkMetadata, get back embeddings from OpenAI in batches
(not one call per chunk — OpenAI's embeddings endpoint accepts a list of
texts per call, so we batch to cut down on API round trips), and pair
each vector with its chunk to build a VectorRecord.
"""

from typing import List

from openai import OpenAI

from config.settings import settings
from core.reporting import reporter
from schemas.step import StepResult, StepStatus

from schemas.chunk_schema import ChunkMetadata, ChunkPayload
from schemas.chunk_schema import VectorRecord
from schemas.document_schema import DocumentMetadata
from schemas.metadata_payload_schema import PayLoad, MetadataPayload
import requests
from exceptions import EmbeddingException
# _client = OpenAI(api_key=settings.openai_api_key)

# BATCH_SIZE = 100

"""
switching to hf embedding model
"""
HF_EMBED_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
headers = {"Authorization": f"Bearer {settings.zeroshot_classification_token_hf}"}


def embed_chunks(chunks: List[ChunkMetadata]) -> List[VectorRecord]:
    vector_records: List[VectorRecord] = []

    # for i in range(0, len(chunks), BATCH_SIZE):
    #     batch = chunks[i:i + BATCH_SIZE]
    #     texts = [c.content for c in batch]

    #     try:
    #         response = _client.embeddings.create(
    #             model=settings.embedding_model,
    #             input=texts,
    #         )
    #     except Exception as e:
    #         reporter.report(StepResult(
    #             step_name="embedding",
    #             status=StepStatus.FAIL,
    #             error_message=str(e),
    #         ))
    #         raise EmbeddingException(reason = str(e))

    #     for chunk, item in zip(batch, response.data):
    #         vector_records.append(VectorRecord(
    #             id=str(chunk.chunk_id),
    #             vector=item.embedding,
    #         ))
    
    for chunk in chunks:
        try:
            response = requests.post(HF_EMBED_URL, headers=headers, json={"inputs": chunk.content})
            vector = response.json()
            print(len(vector))
            vector_records.append(VectorRecord(id=str(chunk.chunk_id), vector=vector))
        except Exception as e:
            reporter.report(StepResult(
                step_name="embedding",
                status=StepStatus.FAIL,
                error_message=str(e),
            ))
            raise EmbeddingException(reason = str(e))
        

    reporter.report(StepResult(
        step_name="embedding",
        status=StepStatus.SUCCESS,
        data={"num_chunks_embedded": len(vector_records)},
    ))
    return vector_records


"""
merges chunk metadata, vectors, and document-level metadata into the
final MetadataPayload objects — one per chunk — ready for Qdrant.
"""


def build_metadata_payloads(
    chunks: List[ChunkMetadata],
    vectors: List[VectorRecord],
    document_metadata: DocumentMetadata,
) -> List[MetadataPayload]:
   
    payloads: List[MetadataPayload] = []

    for chunk, vector_record in zip(chunks, vectors):
        chunk_payload = ChunkPayload(
            vector_record=vector_record,
            chunk_metadata=chunk,
        )
        payload = PayLoad(
            document_payload=document_metadata,
            chunk_payload=chunk_payload,
        )
        payloads.append(MetadataPayload(
            id=chunk.chunk_id,
            payload=payload,
        ))

    return payloads