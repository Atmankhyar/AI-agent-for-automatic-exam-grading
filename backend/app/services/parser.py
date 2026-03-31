"""Extract answers from OCR text by question number."""

import re


QUESTION_MARKER_RE = re.compile(
    r"(?im)^\s*(?:question|q|exercice|exo|probleme|problem)\s*(?:n(?:o|\u00b0)\s*)?(\d{1,3})\s*[:.)\-]?\s*|^\s*(\d{1,3})\s*[:.)\-]\s+",
    re.MULTILINE,
)

_MATH_REPLACEMENTS = {
    "\u2212": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u00d7": "*",
    "\u00f7": "/",
    "\u00b7": "*",
    "\u2219": "*",
    "\u2217": "*",
    "\u221a": "sqrt",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u2248": "~=",
    "\u03c0": "pi",
    "âˆ’": "-",
    "â€“": "-",
    "â€”": "-",
    "Ã—": "*",
    "Ã·": "/",
    "Â·": "*",
    "âˆ™": "*",
    "âˆ—": "*",
    "âˆš": "sqrt",
    "â‰¤": "<=",
    "â‰¥": ">=",
    "â‰ ": "!=",
    "â‰ˆ": "~=",
    "Ï€": "pi",
}
_SUPERSCRIPT_REPLACEMENTS = {
    "\u2070": "^0",
    "\u00b9": "^1",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u2074": "^4",
    "\u2075": "^5",
    "\u2076": "^6",
    "\u2077": "^7",
    "\u2078": "^8",
    "\u2079": "^9",
    "\u207a": "^+",
    "\u207b": "^-",
    "\u207f": "^n",
}
_SUBSCRIPT_REPLACEMENTS = {
    "\u2080": "_0",
    "\u2081": "_1",
    "\u2082": "_2",
    "\u2083": "_3",
    "\u2084": "_4",
    "\u2085": "_5",
    "\u2086": "_6",
    "\u2087": "_7",
    "\u2088": "_8",
    "\u2089": "_9",
}


def parse_submission_text(text: str, num_questions: int = 20, dedupe: str = "last") -> list[dict]:
    """
    Extract answers by question index from OCR text.
    Supports markers like: "Question 1", "Q1", "Exercice 2", "2)", "2.".
    """
    if not text or not text.strip():
        return []

    parts: list[tuple[int, str]] = []
    last_end = 0
    last_q = 0
    max_reasonable_q = max(num_questions * 3, 150)

    for match in QUESTION_MARKER_RE.finditer(text):
        qnum = int(match.group(1) or match.group(2) or "0")
        if qnum <= 0 or qnum > max_reasonable_q:
            continue

        if last_q > 0:
            chunk = text[last_end : match.start()].strip()
            if chunk:
                parts.append((last_q, chunk))

        last_q = qnum
        last_end = match.end()

    if last_q > 0:
        tail = text[last_end:].strip()
        if tail:
            parts.append((last_q, tail))

    if parts:
        # Deduplicate by question index (last block by default).
        by_q: dict[int, str] = {}
        keep_first = dedupe.lower().strip() == "first"
        for qref, chunk in parts:
            if keep_first:
                by_q.setdefault(qref, chunk)
            else:
                by_q[qref] = chunk
        return [
            {
                "question_ref": qref,
                "text": _normalize_answer(chunk),
                "choice": _extract_choice(chunk),
            }
            for qref, chunk in sorted(by_q.items())
        ]

    # Fallback: sequential split by blank-line blocks.
    blocks = _split_into_blocks(text)
    return [
        {
            "question_ref": idx + 1,
            "text": _normalize_answer(block),
            "choice": _extract_choice(block),
        }
        for idx, block in enumerate(blocks[:num_questions])
    ]


def _split_into_blocks(text: str) -> list[str]:
    """Split text into paragraph blocks separated by blank lines."""
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(stripped)

    if current:
        blocks.append("\n".join(current))
    return blocks


def _normalize_answer(raw: str) -> str:
    """Normalize whitespace and math symbols while preserving multi-line answers."""
    if not raw:
        return ""

    out = raw.replace("\r", "")
    out = _normalize_math_text(out)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in out.splitlines()]

    compact: list[str] = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                compact.append("")
            prev_blank = True
            continue
        compact.append(line)
        prev_blank = False

    return "\n".join(compact).strip()


def _normalize_math_text(raw: str) -> str:
    out = raw
    for src, dst in _MATH_REPLACEMENTS.items():
        out = out.replace(src, dst)
    for src, dst in _SUPERSCRIPT_REPLACEMENTS.items():
        out = out.replace(src, dst)
    for src, dst in _SUBSCRIPT_REPLACEMENTS.items():
        out = out.replace(src, dst)

    out = re.sub(r"(?<=\d)\s*[xX]\s*(?=\d)", " * ", out)
    out = re.sub(r"(?<=\d)\s*[/]\s*(?=\d)", " / ", out)
    out = re.sub(r"(?<=\d)\s*-\s*(?=\d)", " - ", out)
    return out


def _extract_choice(raw: str) -> str | None:
    """Extract a single letter (A..F) answer for QCM-style responses."""
    text = (raw or "").strip()
    if not text:
        return None

    normalized = re.sub(r"\s+", " ", text).strip().upper()
    if len(normalized) <= 2 and normalized in "ABCDEF":
        return normalized

    match = re.match(
        r"^(?:REPONSE|R[E\u00c9]PONSE|ANSWER)?\s*[:\-]?\s*[(\[]?\s*([A-F])\s*[)\]\s.:]*$",
        normalized,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).upper()
    return None
