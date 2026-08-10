from app.prompting.formatting.context_formatter import ContextFormatter
from app.prompting.models.prompt import RetrievedContext
from app.retrieval.models.retrieval import RetrievedChunk
from app.textbook_qa.exceptions import UnsupportedGroundingModeError
from app.textbook_qa.models import GroundingMode

# STRICT grounding instructions (PART 12). Deliberately verbose/explicit —
# this is the primary defense layer, backstopped (never solely relied on,
# per PART 12's own instruction) by TextbookAnswerValidator's citation
# resolution/rejection.
_STRICT_SYSTEM_INSTRUCTIONS = """You are a textbook knowledge assistant for Exobios. Answer the \
user's question using ONLY the textbook evidence supplied below.

Do not use outside medical knowledge, training data, or general medical \
reasoning that is not directly supported by the supplied evidence. Do not \
add facts, mechanisms, numbers, or examples that are not present in the \
evidence below, even if they are true and well known to you.

If the supplied evidence does not contain enough information to answer the \
question, set insufficient_evidence to true, and briefly say what is \
missing in the answer field rather than guessing.

Every substantive factual claim in your answer must be followed by a \
citation marker matching a source number below, for example: "the AV node \
delays the impulse [S2]". Only use citation numbers that were actually \
supplied below — never invent a citation number, a book title, a chapter \
name, or a page number. List every citation number you actually used in \
the citations field, and only numbers you used in the answer text."""


def _format_evidence(context: RetrievedContext) -> str:
    if not context.groups:
        return "No relevant textbook evidence was retrieved."

    blocks = []
    for group in context.groups:
        header = f"Source: {group.filename}"
        lines = [f"[S{cited.citation_number}] {cited.chunk.text}" for cited in group.citations]
        blocks.append(header + "\n" + "\n".join(lines))
    return "\n\n".join(blocks)


class TextbookPromptBuilder:
    """Builds the strict-grounding textbook Q&A prompt from a question and
    already-retrieved chunks. Deliberately separate from RagPromptBuilder
    (built around PatientContext/vitals/symptoms — the clinical assessment
    shape, not a knowledge lookup). Reuses ContextFormatter as-is: it has no
    clinical-specific logic, only generic dedup/sort/numbering/grouping.
    """

    def __init__(self, context_formatter: ContextFormatter) -> None:
        self._formatter = context_formatter

    def build(
        self, question: str, chunks: list[RetrievedChunk], mode: GroundingMode
    ) -> tuple[str, RetrievedContext]:
        if mode is not GroundingMode.STRICT:
            raise UnsupportedGroundingModeError(mode=mode.value)

        context = self._formatter.format(chunks)
        evidence_text = _format_evidence(context)

        prompt = (
            f"{_STRICT_SYSTEM_INSTRUCTIONS}\n\n"
            f"## Textbook Evidence\n{evidence_text}\n\n"
            f"## Question\n{question}"
        )
        return prompt, context
