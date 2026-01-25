"""
Document model
"""

from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..db.base import Base


class Document(Base):
    """Document model for uploaded files"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    # Classification
    type = Column(String(50), nullable=False, index=True)  # invoice, reminder, contract, receipt, other
    title = Column(String(255))

    # Metadata (flexible JSON storage)
    doc_metadata = Column(JSON, default={})

    # Processing
    processing_status = Column(String(50), default="pending", index=True)  # pending, processing, done, failed
    confidence_score = Column(Float)
    extracted_text = Column(Text)

    # Timestamps
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="documents")
    file = relationship("File", back_populates="document")
    tasks = relationship("Task", back_populates="document")

    def __repr__(self):
        return f"<Document {self.title} ({self.type})>"
