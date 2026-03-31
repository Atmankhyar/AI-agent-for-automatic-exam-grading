import uuid
from sqlalchemy import Column, ForeignKey, String, JSON, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # qcm | open | code | qru
    prompt = Column(String, nullable=False)
    choices = Column(JSON, nullable=True)  # pour QCM
    answer_key = Column(JSON, nullable=True)  # clé ou solution attendue
    rubric_json = Column(JSON, nullable=True)  # critères pondérés
    max_points = Column(Float, default=1.0)
    order = Column(Integer, default=0)

    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
