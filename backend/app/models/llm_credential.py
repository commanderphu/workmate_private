"""
Stored OAuth credentials for LLM providers
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from ..db.base import Base


class LLMCredential(Base):
    """One row per provider, shared by backend and Celery workers.

    The row lock serializes refreshes: refresh tokens rotate, so two processes
    refreshing at once would invalidate the session.
    """

    __tablename__ = "llm_credentials"

    provider = Column(String, primary_key=True)
    payload = Column(Text, nullable=False)  # Fernet-encrypted JSON, never plaintext (SQL echo logs parameters)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
