from sqlalchemy import inspect, text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_user_by_email
from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import ClassEnrollment, Classroom, User

settings = get_settings()

# Create tables for dev (replace with Alembic in prod).
Base.metadata.create_all(bind=engine)


def _ensure_sqlite_columns() -> None:
    db_url = settings.database_url_resolved
    if not db_url.startswith("sqlite"):
        return

    additions: dict[str, list[tuple[str, str]]] = {
        "users": [
            ("full_name", "TEXT"),
        ],
        "exams": [
            ("class_id", "TEXT"),
            ("statement_file_uri", "TEXT"),
            ("statement_text", "TEXT"),
            ("manual_statement", "TEXT"),
            ("correction_file_uri", "TEXT"),
            ("correction_text", "TEXT"),
        ],
    }

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table_name, columns in additions.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {c["name"] for c in inspector.get_columns(table_name)}
            for col_name, col_type in columns:
                if col_name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))


def _seed_default_data() -> None:
    db = SessionLocal()
    try:
        teacher = get_user_by_email(db, "enseignant@example.com")
        if not teacher:
            teacher = User(
                email="enseignant@example.com",
                hashed_password=hash_password("enseignant123"),
                role="teacher",
                full_name="Enseignant Demo",
            )
            db.add(teacher)
            db.flush()

        student = get_user_by_email(db, "eleve@example.com")
        if not student:
            student = User(
                email="eleve@example.com",
                hashed_password=hash_password("eleve123"),
                role="student",
                full_name="Eleve Demo",
            )
            db.add(student)
            db.flush()

        classroom = (
            db.query(Classroom)
            .filter(Classroom.owner_id == teacher.id, Classroom.name == "Classe Demo")
            .first()
        )
        if not classroom:
            classroom = Classroom(name="Classe Demo", description="Classe de test", owner_id=teacher.id)
            db.add(classroom)
            db.flush()

        enrollment = (
            db.query(ClassEnrollment)
            .filter(ClassEnrollment.class_id == classroom.id, ClassEnrollment.student_id == student.id)
            .first()
        )
        if not enrollment:
            db.add(ClassEnrollment(class_id=classroom.id, student_id=student.id))

        db.commit()
    finally:
        db.close()


app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    _ensure_sqlite_columns()
    Base.metadata.create_all(bind=engine)
    _seed_default_data()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
