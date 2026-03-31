import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="teacher")  # teacher | student | admin
    full_name = Column(String, nullable=True)

    submissions = relationship("Submission", back_populates="student")
    exams = relationship("Exam", back_populates="owner")
    owned_classes = relationship("Classroom", back_populates="owner", cascade="all,delete")
    class_enrollments = relationship("ClassEnrollment", back_populates="student", cascade="all,delete")
