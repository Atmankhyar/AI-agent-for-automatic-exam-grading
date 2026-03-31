import uuid

from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True, index=True)
    statement_file_uri = Column(String, nullable=True)
    statement_text = Column(String, nullable=True)
    manual_statement = Column(String, nullable=True)
    correction_file_uri = Column(String, nullable=True)
    correction_text = Column(String, nullable=True)
    config_json = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="exams")
    classroom = relationship("Classroom", back_populates="exams")
    questions = relationship("Question", back_populates="exam", cascade="all,delete")
    submissions = relationship("Submission", back_populates="exam")

    @property
    def class_name(self) -> str | None:
        return self.classroom.name if self.classroom else None
