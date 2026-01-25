"""
File model
"""

from sqlalchemy import Column, String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..db.base import Base


class File(Base):
    """File storage model"""

    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File Info
    path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    checksum = Column(String(64), index=True)  # SHA256

    # Storage
    storage_backend = Column(String(50), default="local")  # local, s3

    # Processing
    thumbnail_path = Column(String(500))
    extracted_text = Column(Text)
    ocr_language = Column(String(10))

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="files")
    document = relationship("Document", back_populates="file", uselist=False)

    def __repr__(self):
        return f"<File {self.original_filename}>"
