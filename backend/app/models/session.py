"""
Session model
"""

from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import hashlib

from ..db.base import Base


class Session(Base):
    """User session model"""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(255))

    # Device Info
    device_type = Column(String(50))  # web, android, ios
    device_name = Column(String(100))
    os = Column(String(50))
    user_agent = Column(Text)

    # Location
    ip_address = Column(String(45))  # IPv6 compatible
    city = Column(String(100))
    country = Column(String(2))  # ISO Country Code

    # Security
    is_suspicious = Column(Boolean, default=False, index=True)

    # Status
    expires_at = Column(DateTime, nullable=False, index=True)
    last_active = Column(DateTime, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def __repr__(self):
        return f"<Session {self.device_type} for user {self.user_id}>"
