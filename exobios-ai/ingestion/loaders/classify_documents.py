"""
for every document in the db
figure out a way to get these tags filled:

 "complaint_category": "FEVER",
 "applicable_roles": ["ASHA", "DOCTOR"],

classification: zero shot classification using frontier models -> hugging face zero shot classifier
meta data: skip it, not useful, as we will have chunk meta data
"""

import re
import requests
import time
from typing import List
from docling_core.types.doc import DoclingDocument
from exceptions import DocumentClassificationError
from schemas.step import StepResult, StepStatus

from config.settings import settings
from core.reporting import reporter

API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
headers = {
    "Authorization": f"Bearer {settings.zeroshot_classification_token_hf}",
}

# Natural-language phrasing matters here — the underlying NLI model tests
# each label as "This example is {label}." Bare enum-style tokens like
# "FEVER" or "DOCTOR" don't read as real sentences and produce muted,
# unreliable scores. Map enum -> natural phrase for the API call, then
# map the returned phrase back to the enum for storage.
CATEGORY_LABEL_MAP = {
    "FEVER": "fever",
    "RESPIRATORY": "respiratory illness",
    "GASTROINTESTINAL": "gastrointestinal illness",
    "CHILD_HEALTH": "child health",
}
ROLE_LABEL_MAP = {
    "DOCTOR": "intended for a doctor",
    "COMMUNITY_HEALTH_WORKER": "intended for a community health worker",
}

MAX_WORDS = 600
SENTENCES_PER_SECTION = 2


def extract_title(docling_document: DoclingDocument) -> str:
    for item, level in docling_document.iterate_items():
        if item.label == "title":
            return item.text
    for item, level in docling_document.iterate_items():
        if item.label == "section_header":
            return item.text
    return "Untitled Document - please refer the actual document"


def _first_sentences(text: str, n: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:n])


def extract_sections_with_snippets(docling_document: DoclingDocument, max_words: int = MAX_WORDS) -> str:
    """Walk the document in order, pairing each heading with the first
    1-2 sentences of the text that follows it, stopping once a total
    word budget is reached — keeps input safely under the classifier's
    token limit while still carrying real content signal, not just
    generic heading text."""

    parts: List[str] = []
    word_count = 0
    current_heading = None
    heading_used = False

    for item, level in docling_document.iterate_items():
        if word_count >= max_words:
            break

        if item.label == "section_header":
            current_heading = item.text
            heading_used = False
            parts.append(current_heading)
            word_count += len(current_heading.split())

        elif item.label in ("paragraph", "text", "list_item") and current_heading and not heading_used:
            snippet = _first_sentences(item.text, SENTENCES_PER_SECTION)
            if snippet:
                parts.append(snippet)
                word_count += len(snippet.split())
                heading_used = True  # only take one snippet per section

    return ". ".join(parts)


def query(payload: dict) -> dict:
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def _classify_against(text: str, label_map: dict) -> dict:
    """Runs one zero-shot call against a natural-language label set,
    no multi_label — scores come back as a softmax over the given
    candidates (sum to 1), which gives a meaningful relative ranking
    for a "which one primarily applies" question, rather than tiny
    independent probabilities. Returns scores keyed by the original
    enum name, not the phrase sent to the API."""
    phrases = list(label_map.values())
    result = query({
        "inputs": text,
        "parameters": {"candidate_labels": phrases},
    })

    phrase_to_enum = {v: k for k, v in label_map.items()}
    return {phrase_to_enum[item["label"]]: item["score"] for item in result}


def classify(docling_document: DoclingDocument) -> dict:
    title = extract_title(docling_document)
    body = extract_sections_with_snippets(docling_document)
    combined_text = f"{title}. {body}"


    try:
        category_scores = _classify_against(combined_text, CATEGORY_LABEL_MAP)
        # sleep to avoid rate limits
        time.sleep(0.5)
        role_scores = _classify_against(combined_text, ROLE_LABEL_MAP)
        time.sleep(0.5)

        reporter.report(StepResult(
            step_name="classify",
            status=StepStatus.SUCCESS,
            data={"title": title, "category_scores": category_scores, "role_scores": role_scores},
        ))

        return {"title": title, "category_scores": category_scores, "role_scores": role_scores}

    except DocumentClassificationError as e:
        reporter.report(StepResult(
            step_name="classify",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        raise