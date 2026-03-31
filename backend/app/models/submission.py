import uuid
from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    file_uri = Column(String, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending|processing|done|error

    exam = relationship("Exam", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    answers = relationship("Answer", back_populates="submission", cascade="all,delete")
    score = relationship("Score", back_populates="submission", uselist=False)
