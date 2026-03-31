"""Helpers to build per-question exam config from statement/correction text."""

from __future__ import annotations

import re
from typing import Any

from app.services.parser import parse_submission_text

_GENERIC_PROMPT_RE = re.compile(r"^\s*question\s*\d+\s*$", re.IGNORECASE)
_QCM_KEY_PATTERNS = [
    re.compile(
        r"\b(?:bonne\s*)?r[eé]ponse(?:\s*attendue)?\s*[:\-]?\s*([A-F])\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bchoix\s*[:\-]?\s*([A-F])\b", re.IGNORECASE),
]
_CODE_LINE_RE = re.compile(r"(?im)^\s*(?:def|class|function|public|private|for|while|if|elif|else|return)\b")
_POINTS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:points?|pts?)\b", re.IGNORECASE)
_TOTAL_RE = re.compile(r"\btotal\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*(?:points?|pts?)\b", re.IGNORECASE)
_ANSWER_START_RE = re.compile(r"(?im)^\s*(?:reponse\s+attendue.*|reponse\s+possible.*|correction)\s*:\s*$")
_BAREME_LINE_RE = re.compile(r"(?im)^\s*(?:bareme|notation|points?\s*:)\b")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_placeholder_manual(manual_questions: list[dict]) -> bool:
    if not manual_questions:
        return False

    for idx, item in enumerate(manual_questions, start=1):
        prompt = _safe_text(item.get("prompt")).lower()
        answer_key = item.get("answer_key")
        max_points = _to_float(item.get("max_points"), 1.0)

        generic_prompt = (
            not prompt
            or _GENERIC_PROMPT_RE.match(prompt) is not None
            or prompt in {f"q{idx}", f"q {idx}"}
        )
        if not generic_prompt:
            return False
        if not _is_blank(answer_key):
            return False
        if abs(max_points - 1.0) > 1e-9:
            return False
    return True


def extract_question_sections(text: str, num_questions: int = 80) -> list[dict]:
    """Extract numbered blocks from document text."""
    sections = parse_submission_text(text or "", num_questions=num_questions, dedupe="first")
    cleaned: list[dict] = []
    for section in sections:
        try:
            qref = int(section.get("question_ref") or 0)
        except (TypeError, ValueError):
            qref = 0
        if qref <= 0:
            continue
        cleaned.append(
            {
                "question_ref": qref,
                "text": _safe_text(section.get("text")),
                "choice": section.get("choice"),
            }
        )
    return cleaned


def _extract_qcm_answer_key(correction_text: str) -> str | None:
    text = _safe_text(correction_text)
    if not text:
        return None

    first_line = text.splitlines()[0].strip()
    short = re.match(r"^\s*[(\[]?\s*([A-F])\s*[)\]]?\s*$", first_line, re.IGNORECASE)
    if short:
        return short.group(1).upper()

    for pattern in _QCM_KEY_PATTERNS:
        match = pattern.search(text[:300])
        if match:
            return match.group(1).upper()
    return None


def _clean_open_answer_key(correction_text: str) -> str | None:
    text = _safe_text(correction_text)
    if not text:
        return None

    lines = [line.rstrip() for line in text.splitlines()]
    if lines and re.match(r"^\s*\([^)]*points?\)\s*$", lines[0], re.IGNORECASE):
        lines = lines[1:]

    start_idx = 0
    for idx, line in enumerate(lines):
        if _ANSWER_START_RE.match(line):
            start_idx = idx + 1
            break

    kept: list[str] = []
    for line in lines[start_idx:]:
        if _BAREME_LINE_RE.match(line):
            break
        stripped = line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^[\-*•]\s*", "", stripped)
        kept.append(stripped)

    if kept:
        out = "\n".join(kept).strip()
        return out or None

    fallback = "\n".join(line.strip() for line in lines if line.strip()).strip()
    return fallback or None


def _clean_code_answer_key(correction_text: str) -> str | None:
    text = _safe_text(correction_text)
    if not text:
        return None

    lines = [line.rstrip() for line in text.splitlines()]
    start_idx = None

    for idx, line in enumerate(lines):
        if re.match(r"(?i)^\s*reponse\s+possible.*:\s*$", line):
            start_idx = idx + 1
            break
    if start_idx is None:
        for idx, line in enumerate(lines):
            if _CODE_LINE_RE.match(line):
                start_idx = idx
                break
    if start_idx is None:
        start_idx = 0

    kept: list[str] = []
    for line in lines[start_idx:]:
        if _BAREME_LINE_RE.match(line):
            break
        if not line.strip() and not kept:
            continue
        kept.append(line)

    out = "\n".join(kept).strip()
    return out or None


def _looks_like_code(text: str) -> bool:
    lines = [line.rstrip() for line in _safe_text(text).splitlines() if line.strip()]
    if not lines:
        return False

    score = 0
    for line in lines[:24]:
        if _CODE_LINE_RE.match(line):
            score += 2
        if re.search(r"[{};]", line):
            score += 1
        if re.search(r"\b\w+\s*=\s*[^=]", line):
            score += 1
    return score >= 3


def _extract_points_hint(*texts: str) -> float | None:
    for raw in texts:
        text = _safe_text(raw)
        if not text:
            continue
        match = _POINTS_RE.search(text)
        if not match:
            continue
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            continue
    return None


def _extract_total_points(*texts: str) -> float | None:
    for raw in texts:
        text = _safe_text(raw)
        if not text:
            continue
        match = _TOTAL_RE.search(text[:1500])
        if not match:
            continue
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            continue
    return None


def _infer_question_type(statement_text: str, correction_text: str, inferred_choice: str | None) -> str:
    statement = _safe_text(statement_text).lower()
    correction = _safe_text(correction_text)
    if inferred_choice:
        return "qcm"
    if "qru" in statement or "choix unique" in statement:
        return "qru"
    if any(token in statement for token in ["qcm", "choix multiple"]):
        return "qcm"
    if any(token in statement for token in ["code", "programme", "algorithme", "script"]):
        return "code"
    if _looks_like_code(correction):
        return "code"
    return "open"


def _build_prompt(statement_text: str, question_ref: int) -> str:
    text = _safe_text(statement_text)
    if not text:
        return f"Question {question_ref}"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"Question {question_ref}"

    prompt = " ".join(lines[:2])
    prompt = re.sub(r"^\(\s*[^)]*points?\s*\)\s*", "", prompt, flags=re.IGNORECASE)
    if len(prompt) > 320:
        prompt = f"{prompt[:317]}..."
    return prompt


def build_auto_questions_from_texts(
    statement_text: str,
    correction_text: str,
    default_max_points: float = 1.0,
) -> list[dict]:
    """Generate question config per question index from statement/correction text."""
    statement_sections = extract_question_sections(statement_text or "")
    correction_sections = extract_question_sections(correction_text or "")

    statement_by_ref = {int(item["question_ref"]): _safe_text(item.get("text")) for item in statement_sections}
    correction_by_ref = {int(item["question_ref"]): item for item in correction_sections}

    refs = sorted(set(statement_by_ref.keys()) | set(correction_by_ref.keys()))
    auto_questions: list[dict] = []

    for order, qref in enumerate(refs):
        stmt = statement_by_ref.get(qref, "")
        corr_item = correction_by_ref.get(qref, {})
        corr_text = _safe_text(corr_item.get("text"))
        corr_choice = corr_item.get("choice")
        choice = corr_choice.upper() if isinstance(corr_choice, str) and corr_choice.strip() else None
        choice = choice or _extract_qcm_answer_key(corr_text)
        qtype = _infer_question_type(stmt, corr_text, choice)
        points_hint = _extract_points_hint(stmt, corr_text)

        if qtype in {"qcm", "qru"}:
            answer_key: Any = choice
        elif qtype == "code":
            answer_key = _clean_code_answer_key(corr_text) or corr_text or None
        else:
            answer_key = _clean_open_answer_key(corr_text) or corr_text or None

        auto_questions.append(
            {
                "type": qtype,
                "prompt": _build_prompt(stmt, qref),
                "choices": None,
                "answer_key": answer_key,
                "rubric_json": None,
                "max_points": float(points_hint if points_hint is not None else default_max_points),
                "order": order,
            }
        )

    if auto_questions and all(float(q.get("max_points", default_max_points)) == float(default_max_points) for q in auto_questions):
        total_points = _extract_total_points(statement_text, correction_text)
        if total_points and total_points > 0:
            per_question = round(total_points / len(auto_questions), 2)
            for q in auto_questions:
                q["max_points"] = per_question

    return auto_questions


def merge_manual_and_auto_questions(
    manual_questions: list[dict],
    auto_questions: list[dict],
    correction_text: str,
) -> list[dict]:
    """Fill missing manual fields with auto extraction and append missing questions."""
    fallback_correction = _safe_text(correction_text)

    if not manual_questions:
        if auto_questions:
            return auto_questions
        return [
            {
                "type": "open",
                "prompt": "Question 1",
                "choices": None,
                "answer_key": fallback_correction or "A definir",
                "rubric_json": None,
                "max_points": 20.0,
                "order": 0,
            }
        ]

    if auto_questions and _is_placeholder_manual(manual_questions):
        return auto_questions

    merged: list[dict] = []
    for idx, manual in enumerate(manual_questions):
        auto = auto_questions[idx] if idx < len(auto_questions) else {}

        manual_type = _safe_text(manual.get("type")).lower()
        auto_type = _safe_text(auto.get("type")).lower() or "open"
        qtype = manual_type or auto_type
        if qtype not in {"qcm", "qru", "open", "code"}:
            qtype = auto_type

        manual_answer_key = manual.get("answer_key")
        if manual_type in {"qcm", "qru"} and _is_blank(manual_answer_key) and auto_type in {"open", "code"}:
            qtype = auto_type

        prompt = _safe_text(manual.get("prompt"))
        auto_prompt = _safe_text(auto.get("prompt"))
        if not prompt or _GENERIC_PROMPT_RE.match(prompt):
            prompt = auto_prompt or f"Question {idx + 1}"

        answer_key: Any = manual_answer_key
        if _is_blank(answer_key):
            answer_key = auto.get("answer_key")
        if _is_blank(answer_key) and qtype in {"open", "code"} and fallback_correction:
            answer_key = fallback_correction

        merged.append(
            {
                "type": qtype,
                "prompt": prompt,
                "choices": manual.get("choices"),
                "answer_key": answer_key,
                "rubric_json": manual.get("rubric_json"),
                "max_points": _to_float(manual.get("max_points"), _to_float(auto.get("max_points"), 1.0)),
                "order": idx,
            }
        )

    # Append extra auto-extracted questions not covered manually.
    if len(auto_questions) > len(merged):
        for idx in range(len(merged), len(auto_questions)):
            auto = auto_questions[idx]
            merged.append(
                {
                    "type": _safe_text(auto.get("type")).lower() or "open",
                    "prompt": _safe_text(auto.get("prompt")) or f"Question {idx + 1}",
                    "choices": auto.get("choices"),
                    "answer_key": auto.get("answer_key"),
                    "rubric_json": auto.get("rubric_json"),
                    "max_points": _to_float(auto.get("max_points"), 1.0),
                    "order": idx,
                }
            )

    return merged
