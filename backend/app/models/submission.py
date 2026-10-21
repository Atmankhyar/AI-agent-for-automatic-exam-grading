import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models._types import utcnow


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        # The same file cannot be submitted twice for the same student and exam.
        UniqueConstraint("exam_id", "student_id", "file_sha256", name="uq_submission_file"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    file_uri = Column(String, nullable=False)  # storage key (relative to FILE_STORAGE_PATH)
    file_sha256 = Column(String(64), nullable=True, index=True)
    parsed_json = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending|queued|processing|done|error
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=True)

    exam = relationship("Exam", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all,delete")
    score = relationship("Score", back_populates="submission", uselist=False)
    jobs = relationship("GradingJob", back_populates="submission", cascade="all,delete")
