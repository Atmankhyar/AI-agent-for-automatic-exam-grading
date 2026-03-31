"""Pipeline extraction -> traitement par question avant evaluation."""

from typing import Any, Iterable

from app.services.parser import parse_submission_text


def extract_answers_by_question(text: str, num_questions: int) -> list[dict]:
    """Etape 1: extraction des reponses detectees dans la copie."""
    return parse_submission_text(text or "", num_questions=num_questions)


def map_answers_to_exam_questions(
    extracted_answers: list[dict],
    questions_by_order: Iterable[Any],
) -> list[dict]:
    """
    Etape 2: alignement des reponses extraites avec les questions de l'examen.
    Retourne une entree par question d'examen (meme si reponse vide).
    """
    by_ref: dict[int, dict] = {}
    for item in extracted_answers:
        try:
            qref = int(item.get("question_ref") or 0)
        except (TypeError, ValueError):
            qref = 0
        if qref > 0:
            by_ref[qref] = item

    mapped: list[dict] = []
    for idx, q in enumerate(list(questions_by_order), start=1):
        source = by_ref.get(idx, {})
        text = str(source.get("text") or "").strip()
        choice = source.get("choice")
        qtype = str(getattr(q, "type", "open") or "open").lower()

        item = {
            "question_ref": idx,
            "question_id": getattr(q, "id"),
            "text": text,
            "choice": None,
            "code": None,
        }

        if qtype in {"qcm", "qru"}:
            item["choice"] = choice
        elif qtype == "code":
            item["code"] = text
        mapped.append(item)

    return mapped
