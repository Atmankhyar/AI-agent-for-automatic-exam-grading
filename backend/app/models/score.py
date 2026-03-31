import uuid
from sqlalchemy import Column, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), unique=True)
    total = Column(Float, default=0.0)
    breakdown = Column(JSON, nullable=True)  # résumé par question
    feedback = Column(JSON, nullable=True)

    submission = relationship("Submission", back_populates="score")
    items = relationship("ScoreItem", back_populates="score", cascade="all,delete")


class ScoreItem(Base):
    __tablename__ = "score_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    score_id = Column(UUID(as_uuid=True), ForeignKey("scores.id"))
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=True)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    points = Column(Float, default=0.0)
    feedback = Column(JSON, nullable=True)

    score = relationship("Score", back_populates="items")
    answer = relationship("Answer", back_populates="score_items")
