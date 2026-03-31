"""Evaluation logic with detailed feedback per question."""

import re
from difflib import SequenceMatcher
from typing import Any, Dict

from app.services.llm import score_open_answer


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def _extract_qcm_choice(answer_text: str) -> str | None:
    s = (answer_text or "").strip().upper()
    if not s:
        return None
    if len(s) <= 2 and s in "ABCDEF":
        return s
    m = re.match(r"^(?:REPONSE|R[EÉ]PONSE|ANSWER)?\s*[:\-]?\s*[(\[]?\s*([A-F])\s*[)\]\s.:]*$", s, re.I)
    if m:
        return m.group(1).upper()
    return None


def score_qcm(answer_payload: Any, answer_key: Any, max_points: float) -> dict:
    expected = str(answer_key).strip() if answer_key is not None else "-"
    student = str(answer_payload).strip() if answer_payload is not None else ""

    if not student:
        return {
            "points": 0.0,
            "feedback": "Aucune reponse donnee.",
            "correction": f"Reponse attendue: {expected}. Reponse etudiant: (vide).",
            "reponse_etudiant": "(vide)",
            "reponse_attendue": expected,
        }

    is_correct = student.upper() == expected.upper()
    points = max_points if is_correct else 0.0
    return {
        "points": points,
        "feedback": "Correct" if is_correct else "Incorrect",
        "correction": (
            f"Correct. Bonne reponse: {expected}."
            if is_correct
            else f"Incorrect. Reponse attendue: {expected}. Votre reponse: {student}."
        ),
        "reponse_etudiant": student,
        "reponse_attendue": expected,
    }


async def _score_open(question: Dict, answer: Dict, max_points: float, answer_key: Any) -> dict:
    text = (answer.get("text") or "").strip()
    result = await score_open_answer(question, text)
    expected = str(answer_key).strip() if answer_key else "(voir corrige)"
    similarity = _similarity(text, expected) if answer_key else 0.0

    if not text:
        result["points"] = 0.0
        result["feedback"] = "Aucune reponse donnee."

    if "points" not in result:
        result["points"] = 0.0

    result["points"] = float(result["points"])
    result["points"] = min(max(result["points"], 0.0), max_points)

    heuristic_points = round(max_points * similarity, 2) if similarity > 0 else 0.0
    if result["points"] < heuristic_points:
        result["points"] = heuristic_points
        result["feedback"] = result.get("feedback") or "Points ajustes par similarite heuristique."
        result["correction"] = (
            result.get("correction")
            or f"Similarite {round(similarity * 100, 1)}% avec la reponse attendue."
        )

    result["correction"] = result.get(
        "correction",
        f"Points: {result['points']}/{max_points}. Reponse attendue: {expected}.",
    )
    result["reponse_etudiant"] = text or "(vide)"
    result["reponse_attendue"] = expected
    return result


def _score_code(answer: Dict, answer_key: Any, max_points: float) -> dict:
    student_code = (answer.get("code") or answer.get("text") or "").strip()
    expected_code = str(answer_key).strip() if answer_key else ""

    if not student_code:
        return {
            "points": 0.0,
            "feedback": "Aucun code soumis.",
            "correction": "Aucun code detecte dans la copie.",
            "reponse_etudiant": "(vide)",
            "reponse_attendue": expected_code or "-",
        }

    ratio = _similarity(student_code, expected_code) if expected_code else 0.6
    points = round(max_points * ratio, 2)

    if expected_code:
        correction = (
            f"Similarite avec la solution: {round(ratio * 100, 1)}%. "
            f"Points: {points}/{max_points}."
        )
    else:
        correction = (
            f"Correction heuristique sans solution de reference. "
            f"Points: {points}/{max_points}."
        )

    return {
        "points": points,
        "feedback": "Evaluation code terminee",
        "correction": correction,
        "reponse_etudiant": student_code,
        "reponse_attendue": expected_code or "(non defini)",
    }


async def evaluate_answer(question: Dict, answer: Dict) -> dict:
    qtype = (question.get("type") or "open").lower()
    max_points = float(question.get("max_points", 1.0))
    answer_key = question.get("answer_key")

    if qtype in {"qcm", "qru"}:
        text_value = (answer.get("text") or "").strip()
        parsed_from_text = _extract_qcm_choice(text_value)
        if parsed_from_text:
            choice = parsed_from_text
        else:
            raw_choice = answer.get("choice")
            raw = str(raw_choice).strip().upper() if raw_choice is not None else ""
            # Avoid trusting stale parser choices when answer text is clearly not a QCM token.
            choice = raw if len(raw) <= 2 and raw in "ABCDEF" and len(text_value) <= 2 else None
        return score_qcm(choice, answer_key, max_points)

    if qtype == "open":
        return await _score_open(question, answer, max_points, answer_key)

    if qtype == "code":
        return _score_code(answer, answer_key, max_points)

    return {
        "points": 0.0,
        "feedback": "Type de question non supporte",
        "correction": f"Type '{qtype}' non gere.",
        "reponse_etudiant": str(answer.get("text", answer.get("choice", ""))) or "(vide)",
        "reponse_attendue": str(answer_key) if answer_key else "-",
    }
