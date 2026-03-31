import uuid
from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=True)
    choice = Column(JSON, nullable=True)  # peut contenir sélection(s) QCM
    code = Column(String, nullable=True)

    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    score_items = relationship("ScoreItem", back_populates="answer")
