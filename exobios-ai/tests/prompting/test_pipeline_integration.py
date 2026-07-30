from app.core.config import Settings
from app.prompting.factory import build_default_prompt_service
from app.prompting.models.prompt import PromptRequest, PromptSectionName, PromptTemplateName
from app.retrieval.models.retrieval import SearchRequest, SearchResult
from app.retrieval.ranking.reranker import ScoreReranker
from app.retrieval.services.retrieval_service import RetrievalService
from tests.prompting.conftest import make_patient_context
from tests.retrieval.conftest import FakeEmbeddingProvider, FakeRetriever, make_retrieved_chunk


def test_full_prompt_assembly_with_real_retrieval_service():
    high = make_retrieved_chunk(
        score=0.95, text="Fever often accompanies infection.", filename="a.pdf"
    )
    low = make_retrieved_chunk(score=0.4, text="General wellness advice.", filename="b.pdf")
    retriever = FakeRetriever(result=SearchResult(chunks=[high, low]))
    embedding_provider = FakeEmbeddingProvider()
    retrieval_service = RetrievalService(
        embedding_provider=embedding_provider, retriever=retriever, reranker=ScoreReranker()
    )

    settings = Settings(
        AI_API_KEY="test-ai-key",
        OPENAI_API_KEY="test-openai-key",
        DEFAULT_PROMPT_TEMPLATE="diagnosis",
    )
    prompt_service = build_default_prompt_service(
        retrieval_service=retrieval_service, settings=settings
    )

    patient = make_patient_context(patient_complaint="fever and fatigue")
    request = PromptRequest(
        patient=patient, search_request=SearchRequest(query="fever and fatigue")
    )
    response = prompt_service.build_prompt(request)

    assert response.metadata.template == PromptTemplateName.DIAGNOSIS
    assert response.metadata.assessment_id == patient.assessment_id
    assert "[1] Fever often accompanies infection." in response.prompt
    assert "[2] General wellness advice." in response.prompt
    assert response.statistics.retrieved_chunk_count == 2
    assert response.statistics.included_chunk_count == 2
    assert response.statistics.discarded_chunk_count == 0
    assert embedding_provider.embedded_texts == ["fever and fatigue"]


def test_low_context_budget_trims_lowest_ranked_chunk_end_to_end():
    high = make_retrieved_chunk(score=0.95, text="word " * 100, filename="a.pdf")
    low = make_retrieved_chunk(score=0.3, text="word " * 100, filename="b.pdf")
    retriever = FakeRetriever(result=SearchResult(chunks=[high, low]))
    embedding_provider = FakeEmbeddingProvider()
    retrieval_service = RetrievalService(
        embedding_provider=embedding_provider, retriever=retriever, reranker=ScoreReranker()
    )

    settings = Settings(
        AI_API_KEY="test-ai-key",
        OPENAI_API_KEY="test-openai-key",
        MAX_CONTEXT_TOKENS=150,
    )
    prompt_service = build_default_prompt_service(
        retrieval_service=retrieval_service, settings=settings
    )

    request = PromptRequest(
        patient=make_patient_context(), search_request=SearchRequest(query="q")
    )
    response = prompt_service.build_prompt(request)

    assert response.statistics.included_chunk_count == 1
    assert response.statistics.discarded_chunk_count == 1
    knowledge_section = next(
        s for s in response.sections if s.name == PromptSectionName.RETRIEVED_KNOWLEDGE
    )
    assert "[1]" in knowledge_section.content
    assert "[2]" not in knowledge_section.content
