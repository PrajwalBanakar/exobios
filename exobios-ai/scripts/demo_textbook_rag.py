"""Interactive textbook RAG demo (AI-7C): ask a question, get a strictly
textbook-grounded answer with citations, or INSUFFICIENT_EVIDENCE. Reads
from the textbook Qdrant collection populated by scripts/ingest_textbooks.py
— run that first.

    python scripts/demo_textbook_rag.py
    python scripts/demo_textbook_rag.py --subject physiology --question "Explain the cardiac cycle"
    python scripts/demo_textbook_rag.py --debug-retrieval
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.core.config import get_settings  # noqa: E402
from app.core.exceptions import AppError  # noqa: E402
from app.ingestion.models.document import Subject  # noqa: E402
from app.retrieval.factory import build_default_retrieval_service  # noqa: E402
from app.retrieval.models.retrieval import RetrievedChunk, SearchRequest  # noqa: E402
from app.textbook_qa.factory import build_default_textbook_qa_service  # noqa: E402
from app.textbook_qa.models import (  # noqa: E402
    TextbookAnswerResult,
    TextbookCitation,
    TextbookQuestionRequest,
)
from app.textbook_qa.service import TextbookQAService  # noqa: E402

_SUBJECT_MENU = [
    ("All", None),
    ("Anatomy", Subject.ANATOMY),
    ("Physiology", Subject.PHYSIOLOGY),
    ("Biochemistry", Subject.BIOCHEMISTRY),
]
_EXIT_WORDS = {"exit", "quit"}
_PREVIEW_CHARS = 150


def _format_citation(citation: TextbookCitation) -> str:
    book = citation.title or (citation.subject.value if citation.subject else "Unknown source")
    parts = [book]

    if citation.chapter_number or citation.chapter_title:
        chapter = f"Chapter {citation.chapter_number}" if citation.chapter_number else "Chapter"
        if citation.chapter_title:
            chapter += f": {citation.chapter_title}"
        parts.append(chapter)
    if citation.section_title:
        parts.append(citation.section_title)

    page_bits = []
    if citation.pdf_page_start is not None:
        page_bits.append(_page_range("PDF", citation.pdf_page_start, citation.pdf_page_end))
    if citation.printed_page_start is not None:
        page_bits.append(
            _page_range("printed", citation.printed_page_start, citation.printed_page_end)
        )
    if page_bits:
        parts.append(", ".join(page_bits))

    return f"[{citation.citation_number}] " + ", ".join(parts)


def _page_range(label: str, start: int, end: int | None) -> str:
    if end is None or end == start:
        return f"{label} p.{start}"
    return f"{label} pp.{start}-{end}"


def _print_result(result: TextbookAnswerResult) -> None:
    print()
    if result.status.value == "INSUFFICIENT_EVIDENCE":
        print("Answer:\nINSUFFICIENT_EVIDENCE")
        if result.refusal_stage == "retrieval":
            print("(no sufficiently relevant textbook evidence was retrieved)")
        else:
            print("(evidence was retrieved, but the model judged it insufficient to answer)")
    else:
        print(f"Answer:\n{result.answer}")
        print("\nSources:")
        for citation in result.citations:
            print(f"  {_format_citation(citation)}")

    print("\nRetrieval:")
    print(f"  {result.retrieved_chunk_count} chunk(s) retrieved")
    print(
        f"  Top score: {result.top_score:.3f}"
        if result.top_score is not None
        else "  Top score: n/a"
    )
    if result.model:
        print(f"  Model: {result.model}")
    if result.latency_ms is not None:
        print(f"  Latency: {result.latency_ms:.0f}ms")


def _print_debug_retrieval(chunks: list[RetrievedChunk]) -> None:
    print("\n--- debug: retrieved candidates ---")
    for rank, chunk in enumerate(chunks, start=1):
        subject = chunk.subject.value if chunk.subject else "-"
        book = chunk.title or chunk.filename
        chapter = chunk.chapter_number or "-"
        pages = f"{chunk.pdf_page_start}-{chunk.pdf_page_end}" if chunk.pdf_page_start else "-"
        preview = chunk.text[:_PREVIEW_CHARS].replace("\n", " ")
        print(
            f"  #{rank} score={chunk.score:.3f} subject={subject} book={book!r} "
            f"chapter={chapter} pages={pages}"
        )
        print(f"      {preview}...")
    print("--- end debug ---")


def _ask(
    qa_service: TextbookQAService,
    retrieval_service,
    question: str,
    subject: Subject | None,
    debug_retrieval: bool,
) -> None:
    print("\nSearching approved Exobios textbooks...")

    # AppError is the shared base for TextbookQAError, retrieval errors, and
    # LLM provider errors (rate limit, timeout, transient 5xx) alike — a
    # real API hiccup must not crash an interactive demo session; the user
    # can just ask again.
    try:
        if debug_retrieval:
            debug_response = retrieval_service.search(
                SearchRequest(query=question, subject=subject, max_returned_chunks=10)
            )
            _print_debug_retrieval(debug_response.results)

        result = qa_service.answer(TextbookQuestionRequest(question=question, subject=subject))
    except AppError as exc:
        print(f"\nRequest failed: {exc}", file=sys.stderr)
        return
    _print_result(result)


def _select_subject_interactively() -> Subject | None:
    print("\nAvailable subjects:")
    for index, (label, _subject) in enumerate(_SUBJECT_MENU, start=1):
        print(f"{index}. {label}")
    while True:
        choice = input("\nSelect subject: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(_SUBJECT_MENU):
            return _SUBJECT_MENU[int(choice) - 1][1]
        print("Please enter a number from the list above.")


def _run_interactive(debug_retrieval: bool) -> None:
    print("=" * 60)
    print("EXOBIOS TEXTBOOK RAG DEMO")
    print("=" * 60)

    settings = get_settings()
    qa_service = build_default_textbook_qa_service(settings=settings)
    retrieval_service = build_default_retrieval_service(
        settings=settings, collection_name=settings.qdrant_textbook_collection, min_score=0.0
    )

    subject = _select_subject_interactively()

    while True:
        print("\nAsk a question (or 'exit'/'quit'):")
        question = input("> ").strip()
        if not question:
            continue
        if question.lower() in _EXIT_WORDS:
            print("Goodbye.")
            return
        _ask(qa_service, retrieval_service, question, subject, debug_retrieval)


def _run_once(subject_arg: str | None, question: str, debug_retrieval: bool) -> None:
    settings = get_settings()
    qa_service = build_default_textbook_qa_service(settings=settings)
    retrieval_service = build_default_retrieval_service(
        settings=settings, collection_name=settings.qdrant_textbook_collection, min_score=0.0
    )
    subject = Subject(subject_arg.upper()) if subject_arg else None
    _ask(qa_service, retrieval_service, question, subject, debug_retrieval)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exobios textbook RAG demo.")
    parser.add_argument(
        "--subject",
        choices=[s.value.lower() for s in Subject],
        default=None,
        help="Omit for all subjects",
    )
    parser.add_argument(
        "--question", default=None, help="Non-interactive: ask one question and exit"
    )
    parser.add_argument(
        "--debug-retrieval",
        action="store_true",
        help="Show ranked retrieval candidates before answering",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()

    if args.question:
        _run_once(args.subject, args.question, args.debug_retrieval)
        return 0

    _run_interactive(args.debug_retrieval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
