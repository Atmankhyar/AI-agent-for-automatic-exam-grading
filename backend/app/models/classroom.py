import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    owner = relationship("User", back_populates="owned_classes")
    enrollments = relationship("ClassEnrollment", back_populates="classroom", cascade="all,delete")
    exams = relationship("Exam", back_populates="classroom")


class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (UniqueConstraint("class_id", "student_id", name="uq_class_student"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    classroom = relationship("Classroom", back_populates="enrollments")
    student = relationship("User", back_populates="class_enrollments")
