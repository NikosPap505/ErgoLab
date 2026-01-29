import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    IMAGE = "image"
    PHOTO = "photo"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_type = Column(Enum(DocumentType), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    annotations = relationship("Annotation", back_populates="document", cascade="all, delete-orphan")


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, default=1)
    annotation_type = Column(String(50), default="canvas")
    content = Column(Text)  # JSON string for canvas data
    annotation_data = Column(Text, nullable=True)  # Legacy field
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="annotations")
