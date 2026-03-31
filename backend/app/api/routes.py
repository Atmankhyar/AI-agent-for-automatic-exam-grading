import csv
import io
import json
import uuid
from pathlib import Path
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models import (
    Answer,
    ClassEnrollment,
    Classroom,
    Exam,
    Question,
    Score,
    ScoreItem,
    Submission,
    User,
)
from app.schemas import (
    ClassScoreItem,
    ClassroomCreate,
    ClassroomOut,
    ExamCreate,
    ExamOut,
    MeOut,
    ScoreOut,
    StudentEnrollRequest,
    StudentOut,
    SubmissionCreate,
    SubmissionOut,
    Token,
    UserCreate,
    UserOut,
)
from app.services import exam_builder, evaluator, ocr
from app.services.question_pipeline import (
    extract_answers_by_question,
    map_answers_to_exam_questions,
)

router = APIRouter()
settings = get_settings()


def _ensure_teacher_or_admin(user: User) -> None:
    if user.role not in {"teacher", "admin"}:
        raise HTTPException(status_code=403, detail="Teacher/Admin access required")


def _class_is_visible_to_user(db: Session, classroom: Classroom, user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return classroom.owner_id == user.id
    return (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.class_id == classroom.id, ClassEnrollment.student_id == user.id)
        .first()
        is not None
    )


def _class_is_editable_by_user(classroom: Classroom, user: User) -> bool:
    if user.role == "admin":
        return True
    return user.role == "teacher" and classroom.owner_id == user.id


def _exam_is_visible_to_user(db: Session, exam: Exam, user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return exam.owner_id == user.id
    if user.role == "student":
        if exam.class_id is None:
            return False
        return (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.class_id == exam.class_id, ClassEnrollment.student_id == user.id)
            .first()
            is not None
        )
    return False


def _exam_is_editable_by_user(exam: Exam, user: User) -> bool:
    if user.role == "admin":
        return True
    return user.role == "teacher" and exam.owner_id == user.id


def _submission_is_visible_to_user(db: Session, submission: Submission, user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return submission.exam and submission.exam.owner_id == user.id
    if user.role == "student":
        return submission.student_id == user.id
    return False


def _save_upload(upload: UploadFile, suffix_fallback: str = ".pdf") -> str:
    storage = Path(settings.file_storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    ext = Path(upload.filename or "file").suffix or suffix_fallback
    path = storage / f"{uuid.uuid4()}{ext}"
    content = upload.file.read()
    path.write_bytes(content)
    return str(path.absolute())


def _delete_file_safe(file_uri: str | None) -> None:
    if not file_uri:
        return
    try:
        path = Path(file_uri)
        if path.exists():
            path.unlink()
    except Exception:
        print(f"[warn] Could not delete file: {file_uri}")


def _extract_text_safe(file_uri: str | None) -> str | None:
    if not file_uri:
        return None
    try:
        return ocr.extract_text(file_uri)
    except Exception:
        print(f"[warn] Text extraction failed for file: {file_uri}")
        return None


def _submission_to_out(submission: Submission) -> SubmissionOut:
    return SubmissionOut(
        id=submission.id,
        exam_id=submission.exam_id,
        class_id=submission.exam.class_id if submission.exam else None,
        class_name=submission.exam.classroom.name if submission.exam and submission.exam.classroom else None,
        exam_title=submission.exam.title if submission.exam else None,
        student_id=submission.student_id,
        student_email=submission.student.email if submission.student else None,
        file_uri=submission.file_uri,
        status=submission.status,
        parsed_json=submission.parsed_json,
    )


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    if deps.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(deps.get_db)):
    user = deps.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=MeOut)
def me(user: User = Depends(deps.get_current_user)):
    return MeOut(id=str(user.id), email=user.email, role=user.role, full_name=user.full_name)


@router.post("/classes", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
def create_classroom(
    class_in: ClassroomCreate,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    _ensure_teacher_or_admin(user)
    classroom = Classroom(name=class_in.name, description=class_in.description, owner_id=user.id)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.get("/classes", response_model=list[ClassroomOut])
def list_classrooms(db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    if user.role == "admin":
        return db.query(Classroom).order_by(Classroom.name).all()
    if user.role == "teacher":
        return db.query(Classroom).filter(Classroom.owner_id == user.id).order_by(Classroom.name).all()
    return (
        db.query(Classroom)
        .join(ClassEnrollment, ClassEnrollment.class_id == Classroom.id)
        .filter(ClassEnrollment.student_id == user.id)
        .order_by(Classroom.name)
        .all()
    )


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(
    class_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_editable_by_user(classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    # Detach exams linked to this class to avoid FK issues and keep them accessible.
    for exam in db.query(Exam).filter(Exam.class_id == class_id).all():
        exam.class_id = None

    db.delete(classroom)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/classes/{class_id}/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def add_student_to_class(
    class_id: uuid.UUID,
    payload: StudentEnrollRequest,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_editable_by_user(classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    student = deps.get_user_by_email(db, payload.email)
    if not student:
        generated_password = payload.password or "eleve123"
        student = User(
            email=payload.email,
            hashed_password=hash_password(generated_password),
            role="student",
            full_name=payload.full_name,
        )
        db.add(student)
        db.flush()
    else:
        if student.role not in {"student", "admin"}:
            raise HTTPException(status_code=400, detail="User exists with non-student role")
        if payload.full_name and not student.full_name:
            student.full_name = payload.full_name

    exists = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.student_id == student.id)
        .first()
    )
    if not exists:
        db.add(ClassEnrollment(class_id=class_id, student_id=student.id))

    db.commit()
    db.refresh(student)
    return student


@router.post("/classes/{class_id}/roster", response_model=list[StudentOut])
async def import_class_roster(
    class_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_editable_by_user(classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    students: list[User] = []

    for row in reader:
        email = (row.get("email") or "").strip()
        if not email:
            continue
        full_name = (row.get("full_name") or "").strip() or None
        password = (row.get("password") or "").strip() or "eleve123"

        student = deps.get_user_by_email(db, email)
        if not student:
            student = User(
                email=email,
                hashed_password=hash_password(password),
                role="student",
                full_name=full_name,
            )
            db.add(student)
            db.flush()
        elif student.role not in {"student", "admin"}:
            continue
        elif full_name and not student.full_name:
            student.full_name = full_name

        exists = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.student_id == student.id)
            .first()
        )
        if not exists:
            db.add(ClassEnrollment(class_id=class_id, student_id=student.id))

        students.append(student)

    db.commit()
    return students


@router.get("/classes/{class_id}/students", response_model=list[StudentOut])
def list_class_students(
    class_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_visible_to_user(db, classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    return (
        db.query(User)
        .join(ClassEnrollment, ClassEnrollment.student_id == User.id)
        .filter(ClassEnrollment.class_id == class_id)
        .order_by(User.email)
        .all()
    )


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_from_class(
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_editable_by_user(classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    enrollment = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.student_id == student_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not found in class")

    db.delete(enrollment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/classes/{class_id}/scores", response_model=list[ClassScoreItem])
def class_scores(
    class_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    classroom = db.get(Classroom, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    if not _class_is_visible_to_user(db, classroom, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    query = (
        db.query(Score, Submission, Exam, User)
        .join(Submission, Score.submission_id == Submission.id)
        .join(Exam, Submission.exam_id == Exam.id)
        .outerjoin(User, Submission.student_id == User.id)
        .filter(Exam.class_id == class_id)
        .order_by(Exam.title)
    )

    if user.role == "student":
        query = query.filter(Submission.student_id == user.id)

    results: list[ClassScoreItem] = []
    for score, submission, exam, student in query.all():
        results.append(
            ClassScoreItem(
                submission_id=submission.id,
                exam_id=exam.id,
                exam_title=exam.title,
                class_id=exam.class_id,
                class_name=classroom.name,
                student_id=submission.student_id,
                student_email=student.email if student else None,
                total=score.total,
            )
        )
    return results


@router.get("/me/scores", response_model=list[ClassScoreItem])
def my_scores(db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    query = (
        db.query(Score, Submission, Exam, Classroom)
        .join(Submission, Score.submission_id == Submission.id)
        .join(Exam, Submission.exam_id == Exam.id)
        .outerjoin(Classroom, Exam.class_id == Classroom.id)
    )

    if user.role == "student":
        query = query.filter(Submission.student_id == user.id)
    elif user.role == "teacher":
        query = query.filter(Exam.owner_id == user.id)

    data: list[ClassScoreItem] = []
    for score, submission, exam, classroom in query.all():
        data.append(
            ClassScoreItem(
                submission_id=submission.id,
                exam_id=exam.id,
                exam_title=exam.title,
                class_id=exam.class_id,
                class_name=classroom.name if classroom else "Sans classe",
                student_id=submission.student_id,
                student_email=submission.student.email if submission.student else None,
                total=score.total,
            )
        )
    return data


@router.get("/exams", response_model=list[ExamOut])
def list_exams(db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    if user.role == "admin":
        return db.query(Exam).order_by(Exam.title).all()
    if user.role == "teacher":
        return db.query(Exam).filter(Exam.owner_id == user.id).order_by(Exam.title).all()
    return (
        db.query(Exam)
        .join(ClassEnrollment, ClassEnrollment.class_id == Exam.class_id)
        .filter(ClassEnrollment.student_id == user.id)
        .order_by(Exam.title)
        .all()
    )


@router.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: uuid.UUID, db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    exam = db.get(Exam, exam_id)
    if not exam or not _exam_is_visible_to_user(db, exam, user):
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(exam_id: uuid.UUID, db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not _exam_is_editable_by_user(exam, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    files_to_delete: list[str] = []
    if exam.statement_file_uri:
        files_to_delete.append(exam.statement_file_uri)
    if exam.correction_file_uri:
        files_to_delete.append(exam.correction_file_uri)

    submissions = db.query(Submission).filter(Submission.exam_id == exam.id).all()
    for submission in submissions:
        if submission.file_uri:
            files_to_delete.append(submission.file_uri)

        score = db.query(Score).filter(Score.submission_id == submission.id).first()
        if score:
            db.delete(score)
            db.flush()

        db.delete(submission)

    db.delete(exam)
    db.commit()

    for file_uri in files_to_delete:
        _delete_file_safe(file_uri)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/exams/from-pdf", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
async def create_exam_from_pdf(
    statement_file: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    correction_file: UploadFile | None = File(None),
    title: str = Form(""),
    description: str = Form(""),
    manual_statement: str = Form(""),
    bareme: str = Form(""),
    class_id: str | None = Form(None),
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    _ensure_teacher_or_admin(user)

    statement_upload = statement_file or file
    if not statement_upload or not statement_upload.filename:
        raise HTTPException(status_code=400, detail="Enonce file is required")
    if not correction_file or not correction_file.filename:
        raise HTTPException(status_code=400, detail="Corrige file is required")

    class_uuid: uuid.UUID | None = None
    if class_id:
        try:
            class_uuid = uuid.UUID(class_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid class_id")
        classroom = db.get(Classroom, class_uuid)
        if not classroom:
            raise HTTPException(status_code=404, detail="Class not found")
        if not _class_is_editable_by_user(classroom, user):
            raise HTTPException(status_code=403, detail="Not allowed")

    statement_file_uri = _save_upload(statement_upload)
    correction_file_uri = _save_upload(correction_file)

    statement_text = _extract_text_safe(statement_file_uri)
    correction_text = _extract_text_safe(correction_file_uri)
    if not statement_text or not statement_text.strip():
        _delete_file_safe(statement_file_uri)
        _delete_file_safe(correction_file_uri)
        raise HTTPException(status_code=400, detail="Impossible d'extraire le texte de l'enonce")
    if not correction_text or not correction_text.strip():
        _delete_file_safe(statement_file_uri)
        _delete_file_safe(correction_file_uri)
        raise HTTPException(status_code=400, detail="Impossible d'extraire le texte du corrige")

    manual_questions: list[dict] = []
    if bareme:
        try:
            parsed = json.loads(bareme)
            if isinstance(parsed, list):
                manual_questions = [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            manual_questions = []

    auto_questions = exam_builder.build_auto_questions_from_texts(
        statement_text=statement_text,
        correction_text=correction_text,
    )
    questions_data = exam_builder.merge_manual_and_auto_questions(
        manual_questions=manual_questions,
        auto_questions=auto_questions,
        correction_text=correction_text,
    )

    exam = Exam(
        title=title or "Examen sans titre",
        description=description or None,
        owner_id=user.id,
        class_id=class_uuid,
        statement_file_uri=statement_file_uri,
        statement_text=statement_text,
        manual_statement=manual_statement or None,
        correction_file_uri=correction_file_uri,
        correction_text=correction_text,
        config_json={"created_via": "from-pdf"},
    )
    db.add(exam)
    db.flush()

    for idx, q in enumerate(questions_data):
        qtype = (q.get("type") or "open")
        answer_key = q.get("answer_key")
        if (
            qtype in {"open", "code"}
            and (answer_key is None or (isinstance(answer_key, str) and not answer_key.strip()))
            and correction_text
        ):
            answer_key = correction_text

        db.add(
            Question(
                exam_id=exam.id,
                type=qtype,
                prompt=(q.get("prompt") or f"Question {idx + 1}"),
                choices=q.get("choices"),
                answer_key=answer_key,
                rubric_json=q.get("rubric_json"),
                max_points=float(q.get("max_points", 1.0)),
                order=int(q.get("order", idx)),
            )
        )

    db.commit()
    db.refresh(exam)
    return exam


@router.post("/exams", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(exam_in: ExamCreate, db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    _ensure_teacher_or_admin(user)

    if exam_in.class_id:
        classroom = db.get(Classroom, exam_in.class_id)
        if not classroom:
            raise HTTPException(status_code=404, detail="Class not found")
        if not _class_is_editable_by_user(classroom, user):
            raise HTTPException(status_code=403, detail="Not allowed")

    exam = Exam(
        title=exam_in.title,
        description=exam_in.description,
        owner_id=user.id,
        class_id=exam_in.class_id,
        statement_file_uri=exam_in.statement_file_uri,
        statement_text=exam_in.statement_text,
        manual_statement=exam_in.manual_statement,
        correction_file_uri=exam_in.correction_file_uri,
        correction_text=exam_in.correction_text,
        config_json=exam_in.config_json,
    )
    db.add(exam)
    db.flush()

    for idx, q in enumerate(exam_in.questions):
        db.add(
            Question(
                exam_id=exam.id,
                type=q.type,
                prompt=q.prompt,
                choices=q.choices,
                answer_key=q.answer_key,
                rubric_json=q.rubric_json,
                max_points=q.max_points,
                order=q.order if q.order is not None else idx,
            )
        )

    db.commit()
    db.refresh(exam)
    return exam


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), user: User = Depends(deps.get_current_user)):
    file_uri = _save_upload(file)
    return {"file_uri": file_uri}


@router.get("/submissions", response_model=list[SubmissionOut])
def list_submissions(
    exam_id: uuid.UUID | None = None,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    query = db.query(Submission).join(Exam)

    if user.role == "teacher":
        query = query.filter(Exam.owner_id == user.id)
    elif user.role == "student":
        query = query.filter(Submission.student_id == user.id)

    if exam_id:
        query = query.filter(Submission.exam_id == exam_id)

    submissions = query.order_by(Submission.id.desc()).all()
    return [_submission_to_out(s) for s in submissions]


@router.post("/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(
    submission_in: SubmissionCreate,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    exam = db.get(Exam, submission_in.exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not _exam_is_visible_to_user(db, exam, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    if user.role == "student":
        student_id = user.id
    else:
        student_id = submission_in.student_id or user.id

    submission = Submission(
        exam_id=submission_in.exam_id,
        student_id=student_id,
        file_uri=submission_in.file_uri,
        status="pending",
        parsed_json=None,
    )
    db.add(submission)
    db.flush()

    if submission_in.answers:
        for ans in submission_in.answers:
            db.add(
                Answer(
                    submission_id=submission.id,
                    question_id=uuid.UUID(ans["question_id"]),
                    text=ans.get("text"),
                    choice=ans.get("choice"),
                    code=ans.get("code"),
                )
            )

    db.commit()
    db.refresh(submission)
    return _submission_to_out(submission)


async def _evaluate_submission(submission_id: uuid.UUID, db: Session):
    submission: Submission = db.get(Submission, submission_id)
    if not submission:
        return

    exam = db.get(Exam, submission.exam_id)
    if not exam:
        submission.status = "error"
        db.commit()
        return

    questions_by_order = sorted(exam.questions, key=lambda q: q.order or 0)
    question_map = {q.id: q for q in exam.questions}
    max_total_points = sum(max(float(q.max_points or 0), 0.0) for q in questions_by_order)
    scale_base = max_total_points if max_total_points > 0 else max(len(questions_by_order), 1)
    scale_factor = 20.0 / scale_base

    def _text_for_similarity(ans: Answer) -> str:
        if ans.text and ans.text.strip():
            return ans.text.strip()
        if ans.code and ans.code.strip():
            return ans.code.strip()
        if ans.choice is not None:
            return str(ans.choice).strip()
        return ""

    def _best_similarity_for_answer(question_id: uuid.UUID, current_answer: Answer) -> dict | None:
        # compare with other submissions' answers to flag potential plagiarism
        candidates = (
            db.query(Answer, Submission)
            .join(Submission, Answer.submission_id == Submission.id)
            .filter(Answer.question_id == question_id, Answer.submission_id != current_answer.submission_id)
            .limit(50)
            .all()
        )
        current_text = _text_for_similarity(current_answer)
        if not current_text:
            return None

        best_ratio = 0.0
        best_payload: dict | None = None

        for other_answer, other_submission in candidates:
            other_text = _text_for_similarity(other_answer)
            if not other_text:
                continue
            ratio = SequenceMatcher(None, current_text.lower(), other_text.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_payload = {
                    "other_submission_id": str(other_submission.id),
                    "other_student_id": str(other_submission.student_id) if other_submission.student_id else None,
                    "ratio": round(ratio, 3),
                }

        if best_ratio >= 0.88:
            return best_payload
        return None

    def _is_empty_answer(ans: Answer) -> bool:
        text = (ans.text or "").strip()
        code = (ans.code or "").strip()
        choice = ans.choice
        choice_empty = choice is None or choice in {"", "null"} or choice == [] or choice == {}
        return not text and not code and choice_empty

    should_parse_from_file = not submission.answers
    if not should_parse_from_file and submission.file_uri:
        should_parse_from_file = all(_is_empty_answer(a) for a in submission.answers)

    if should_parse_from_file:
        for existing in list(submission.answers):
            db.delete(existing)
        db.flush()

        text = _extract_text_safe(submission.file_uri) if submission.file_uri else ""
        extracted = extract_answers_by_question(text or "", num_questions=len(questions_by_order) or 20)
        mapped = map_answers_to_exam_questions(extracted, questions_by_order)

        submission.parsed_json = {
            "extracted": extracted,
            "mapped": [
                {
                    "question_ref": m.get("question_ref"),
                    "question_id": str(m.get("question_id")),
                    "text": m.get("text"),
                    "choice": m.get("choice"),
                }
                for m in mapped
            ],
        }

        for m in mapped:
            db.add(
                Answer(
                    submission_id=submission.id,
                    question_id=m["question_id"],
                    text=m.get("text"),
                    choice=m.get("choice"),
                    code=m.get("code"),
                )
            )

        db.commit()
        db.refresh(submission)

    total = 0.0
    raw_total = 0.0
    items: list[ScoreItem] = []
    breakdown = {}

    for answer in submission.answers:
        question = question_map.get(answer.question_id)
        if not question:
            continue

        question_payload = {
            "id": str(question.id),
            "type": question.type,
            "prompt": question.prompt,
            "choices": question.choices,
            "answer_key": question.answer_key,
            "rubric_json": question.rubric_json,
            "max_points": question.max_points,
            "order": question.order,
        }
        answer_payload = {
            "id": str(answer.id),
            "submission_id": str(answer.submission_id),
            "question_id": str(answer.question_id),
            "text": answer.text,
            "choice": answer.choice,
            "code": answer.code,
        }
        result = await evaluator.evaluate_answer(question_payload, answer_payload)
        max_points_for_question = max(float(question.max_points or 0.0), 0.0)
        raw_points = max(float(result.get("points", 0.0)), 0.0)
        if max_points_for_question > 0:
            raw_points = min(raw_points, max_points_for_question)

        scaled_points = raw_points * scale_factor
        raw_total += raw_points
        total += scaled_points

        plagiarism = _best_similarity_for_answer(question.id, answer)
        if plagiarism:
            result["plagiarism"] = plagiarism

        correction = result.get("correction", result.get("feedback", ""))
        breakdown[str(question.id)] = {
            "points": scaled_points,
            "raw_points": raw_points,
            "max_points": max_points_for_question,
            "feedback": correction,
            "correction": correction,
            "reponse_etudiant": result.get("reponse_etudiant"),
            "reponse_attendue": result.get("reponse_attendue"),
            "plagiarism": plagiarism,
        }

        items.append(
            ScoreItem(
                submission_id=submission.id,
                question_id=question.id,
                answer_id=answer.id,
                points=scaled_points,
                feedback=result,
            )
        )

    old_score = db.query(Score).filter(Score.submission_id == submission.id).first()
    if old_score:
        db.delete(old_score)
        db.flush()

    total_rounded = round(total, 2)
    score = Score(
        submission_id=submission.id,
        total=total_rounded,
        breakdown=breakdown,
        feedback={"scale_factor": scale_factor, "raw_total": raw_total, "max_total": max_total_points},
    )
    db.add(score)
    db.flush()

    for item in items:
        item.score = score
        db.add(item)

    submission.status = "done"
    db.commit()


@router.post("/evaluate/{submission_id}", response_model=ScoreOut)
async def evaluate_submission(
    submission_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_user),
):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    exam = db.get(Exam, submission.exam_id)
    if not exam or not _exam_is_editable_by_user(exam, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    submission.status = "processing"
    db.commit()
    db.refresh(submission)

    await _evaluate_submission(submission_id, db)
    score = db.query(Score).filter(Score.submission_id == submission_id).first()
    if not score:
        raise HTTPException(status_code=500, detail="Scoring failed")
    return score


@router.get("/scores/{submission_id}", response_model=ScoreOut)
def get_score(submission_id: uuid.UUID, db: Session = Depends(deps.get_db), user: User = Depends(deps.get_current_user)):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if not _submission_is_visible_to_user(db, submission, user):
        raise HTTPException(status_code=403, detail="Not allowed")

    score = db.query(Score).filter(Score.submission_id == submission_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not ready")
    return score
