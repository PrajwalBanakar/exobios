"""End-to-end demo: ingest a clinical guideline PDF, then run a sample sick-child
case through retrieval -> prompting -> generation and print the result.

This is a demo/dev script, not part of the FastAPI service — POST /analyze does
not call this pipeline yet (see README's AI-1 scope note). Run from exobios-ai/:

    python scripts/demo_pipeline.py
"""

import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.embeddings.factory import build_default_embedding_service
from app.generation.factory import build_default_generation_service
from app.generation.models.request import GenerationRequest
from app.ingestion.services.factory import build_default_ingestion_service
from app.prompting.factory import build_default_prompt_service
from app.prompting.models.prompt import PatientContext, PromptRequest, PromptTemplateName
from app.retrieval.factory import build_default_retrieval_service
from app.retrieval.models.retrieval import SearchRequest
from app.schemas.analyze import ComplaintCategory, SymptomSummary, VitalsSummary

PDF_PATH = Path(__file__).parent.parent / "imnci_chart_booklet.pdf"


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def _already_ingested(settings) -> bool:
    # The document registry is in-memory and resets every run, but Qdrant is
    # a persistent Docker volume — if it already has vectors from a prior
    # run, re-ingesting would just re-embed identical chunks and burn
    # free-tier embedding quota for nothing.
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    if settings.qdrant_collection not in {c.name for c in client.get_collections().collections}:
        return False
    return client.count(settings.qdrant_collection).count > 0


def main() -> None:
    settings = get_settings()
    provider_name = "Gemini" if settings.gemini_api_key else "OpenAI"
    print(f"Using {provider_name} for embeddings + generation.")

    section("STEP 1 — INGESTION: parsing, chunking, and embedding the IMNCI PDF")
    if _already_ingested(settings):
        print("Qdrant already has vectors from a previous run of this script. Skipping ingestion.")
    else:
        embedding_service = build_default_embedding_service(settings=settings)
        # Larger chunks than the default (1000/150) keep this 39-page PDF's
        # chunk count under Gemini's free-tier embed_content quota (100
        # items/minute), so ingestion fits in a single embedding batch
        # instead of needing to pace multiple requests across a minute.
        ingestion_service = build_default_ingestion_service(
            embedding_service=embedding_service, chunk_size=2000, chunk_overlap=200
        )

        start = time.perf_counter()
        result = ingestion_service.ingest(
            PDF_PATH,
            source="WHO / MoHFW India — Facility Based IMNCI Chart Booklet",
            version="1.0",
            tags=["imnci", "pediatrics", "who", "neonatal", "child-health"],
            language="en",
        )
        print(
            f"Ingested '{result.document.filename}': "
            f"{result.document.page_count} pages -> {result.document.chunk_count} chunks "
            f"in {time.perf_counter() - start:.1f}s"
        )

    section("STEP 2 — SAMPLE CASE: a sick child assessment")
    assessment_id = uuid.uuid4()
    patient = PatientContext(
        assessment_id=assessment_id,
        patient_id=uuid.uuid4(),
        patient_complaint=(
            "18-month-old child brought to the clinic with cough and fast breathing for "
            "3 days, fever since yesterday, and watery diarrhoea since this morning. "
            "Mother reports the child is drinking eagerly and seems thirsty."
        ),
        complaint_category=ComplaintCategory.RESPIRATORY,
        symptoms=[
            SymptomSummary(name="cough", duration="3 days", severity="moderate"),
            SymptomSummary(name="fast breathing", duration="3 days", severity="moderate"),
            SymptomSummary(name="fever", duration="1 day", severity="moderate"),
            SymptomSummary(name="watery diarrhoea", duration="less than 1 day", severity="mild"),
        ],
        vitals=VitalsSummary(
            heart_rate=132,
            temperature=38.6,
            respiratory_rate=52,
            spo2=95,
        ),
    )
    print(patient.patient_complaint)

    section("STEP 3 — RETRIEVAL: finding the relevant IMNCI guidance")
    retrieval_service = build_default_retrieval_service(settings=settings)
    search_request = SearchRequest(
        query=(
            "18 month old child with cough, fast breathing, fever and watery diarrhoea, "
            "drinking eagerly and thirsty — classify pneumonia and dehydration"
        ),
        top_k=20,
        max_returned_chunks=6,
    )

    section("STEP 4 — PROMPTING: assembling the grounded clinical prompt")
    prompt_service = build_default_prompt_service(
        retrieval_service=retrieval_service, settings=settings
    )
    prompt_response = prompt_service.build_prompt(
        PromptRequest(
            patient=patient, search_request=search_request, template=PromptTemplateName.DIAGNOSIS
        )
    )
    print(
        f"Prompt built: {prompt_response.statistics.prompt_tokens} tokens, "
        f"{prompt_response.statistics.included_chunk_count} cited chunks "
        f"(from {prompt_response.statistics.retrieved_chunk_count} retrieved)"
    )

    section("STEP 5 — GENERATION: asking the LLM for a grounded clinical draft")
    generation_service = build_default_generation_service(settings=settings)
    result = generation_service.generate(GenerationRequest(prompt_response=prompt_response))

    section("RESULT")
    output = result.output
    print(f"Summary:\n  {output.summary}\n")

    print("Possible conditions:")
    for cond in output.possible_conditions:
        print(f"  - {cond.name} ({cond.likelihood}): {cond.reasoning}")

    print(f"\nRisk assessment: {output.risk_assessment.level}")
    print(f"  Reasoning: {output.risk_assessment.reasoning}")
    escalation = output.risk_assessment.requires_immediate_escalation
    print(f"  Requires immediate escalation: {escalation}")

    if output.red_flags:
        print("\nRed flags:")
        for flag in output.red_flags:
            print(f"  - [{flag.severity}] {flag.description} -> {flag.action}")

    if output.recommended_actions:
        print("\nRecommended actions:")
        for action in output.recommended_actions:
            print(f"  - [{action.priority}] {action.action}")

    if output.follow_up_questions:
        print("\nFollow-up questions:")
        for q in output.follow_up_questions:
            print(f"  - {q}")

    if output.limitations:
        print("\nLimitations:")
        for lim in output.limitations:
            print(f"  - {lim}")

    print("\nCitations (grounded in the ingested IMNCI PDF):")
    for citation in result.resolved_citations:
        page = f", p.{citation.page_number}" if citation.page_number else ""
        print(f"  [{citation.citation_number}] {citation.filename}{page}")

    print(f"\nModel: {result.metadata.model} | latency: {result.metadata.latency_ms:.0f}ms")


if __name__ == "__main__":
    main()
