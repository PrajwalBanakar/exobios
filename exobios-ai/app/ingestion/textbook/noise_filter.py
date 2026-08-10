import re

_NOISE_LINE_PATTERNS = [
    re.compile(r"^\s*contents\s*$", re.IGNORECASE),
    re.compile(r"^\s*index\s*$", re.IGNORECASE),
    re.compile(r"this\s+page\s+(?:is\s+)?intentionally\s+left\s+blank", re.IGNORECASE),
    re.compile(r"^\s*\d{1,4}\s*$"),
]

_MIN_ALPHA_CHARS = 40


def is_noise_text(text: str, token_count: int, min_useful_tokens: int) -> bool:
    """Conservative noise check applied once per finalized chunk (not per
    line/block) — a chunk is dropped only when it's both short *and* looks
    like boilerplate, so a short but real medical definition ("Homeostasis
    is...", well over _MIN_ALPHA_CHARS) always survives."""
    stripped = text.strip()
    if not stripped:
        return True
    for pattern in _NOISE_LINE_PATTERNS:
        if pattern.fullmatch(stripped):
            return True

    alpha_chars = sum(1 for c in stripped if c.isalpha())
    return token_count < min_useful_tokens and alpha_chars < _MIN_ALPHA_CHARS
