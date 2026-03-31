import re
from difflib import SequenceMatcher


def _normalize_math_text(s: str) -> str:
    if not s:
        return ""

    replacements = {
        "−": "-",
        "–": "-",
        "—": "-",
        "×": "*",
        "÷": "/",
        "·": "*",
        "∙": "*",
        "∗": "*",
        "√": "sqrt",
        "≤": "<=",
        "≥": ">=",
        "≠": "!=",
        "≈": "~=",
        "π": "pi",
    }
    superscripts = {
        "⁰": "^0",
        "¹": "^1",
        "²": "^2",
        "³": "^3",
        "⁴": "^4",
        "⁵": "^5",
        "⁶": "^6",
        "⁷": "^7",
        "⁸": "^8",
        "⁹": "^9",
        "⁺": "^+",
        "⁻": "^-",
        "ⁿ": "^n",
    }
    subscripts = {
        "₀": "_0",
        "₁": "_1",
        "₂": "_2",
        "₃": "_3",
        "₄": "_4",
        "₅": "_5",
        "₆": "_6",
        "₇": "_7",
        "₈": "_8",
        "₉": "_9",
    }
    out = s
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    for src, dst in superscripts.items():
        out = out.replace(src, dst)
    for src, dst in subscripts.items():
        out = out.replace(src, dst)
    out = re.sub(r"\s+", " ", out.strip().lower())
    out = re.sub(r"\s*([+\-*/=()^])\s*", r"\1", out)
    return out


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    raw = SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
    math = SequenceMatcher(None, _normalize_math_text(a), _normalize_math_text(b)).ratio()
    return max(raw, math)


async def score_open_answer(question: dict, answer: str) -> dict:
    """
    Stub scoring for open answers.
    Returns: {points, feedback, criteres[]}.
    """
    rubric = question.get("rubric_json") or []
    max_points = float(question.get("max_points", 1.0))
    answer_key = str(question.get("answer_key") or "").strip()
    answer_clean = answer.strip()

    if not answer_clean:
        points = 0.0
    elif answer_key:
        points = round(max_points * _sim(answer_clean, answer_key), 2)
    else:
        points = round(max_points * 0.7, 2)

    return {
        "points": points,
        "feedback": f"{points}/{max_points} pts" if answer_clean else "Aucune reponse.",
        "criteres": [{"id": c.get("id", "c"), "score": points, "comment": ""} for c in rubric],
    }
