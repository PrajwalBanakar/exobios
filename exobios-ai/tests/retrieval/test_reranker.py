from app.retrieval.ranking.reranker import ScoreReranker
from tests.embeddings.conftest import make_chunk, make_document_metadata
from tests.retrieval.conftest import make_retrieved_chunk


def test_sorts_by_score_descending():
    low = make_retrieved_chunk(score=0.2)
    high = make_retrieved_chunk(score=0.9)
    mid = make_retrieved_chunk(score=0.5)
    reranker = ScoreReranker()

    ranked = reranker.rerank([low, high, mid], max_results=10)

    assert [c.score for c in ranked] == [0.9, 0.5, 0.2]


def test_removes_duplicate_chunk_ids_keeping_highest_score():
    document = make_document_metadata()
    chunk = make_chunk(document.id)
    low = make_retrieved_chunk(document=document, chunk=chunk, score=0.3)
    high = make_retrieved_chunk(document=document, chunk=chunk, score=0.95)
    reranker = ScoreReranker()

    ranked = reranker.rerank([low, high], max_results=10)

    assert len(ranked) == 1
    assert ranked[0].score == 0.95


def test_distinct_chunk_ids_are_not_deduplicated():
    first = make_retrieved_chunk(score=0.6)
    second = make_retrieved_chunk(score=0.7)
    reranker = ScoreReranker()

    ranked = reranker.rerank([first, second], max_results=10)

    assert len(ranked) == 2


def test_limits_to_max_results():
    chunks = [make_retrieved_chunk(score=float(i)) for i in range(5)]
    reranker = ScoreReranker()

    ranked = reranker.rerank(chunks, max_results=2)

    assert len(ranked) == 2
    assert [c.score for c in ranked] == [4.0, 3.0]


def test_empty_input_returns_empty_list():
    reranker = ScoreReranker()

    assert reranker.rerank([], max_results=5) == []
