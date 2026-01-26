"""
Integration model for external services
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class IntegrationType(str, enum.Enum):
    """Type of integration"""
    CALDAV = "caldav"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"


class SyncDirection(str, enum.Enum):
    """Direction of synchronization"""
    TO_CALENDAR = "to_calendar"  # Workmate → External
    FROM_CALENDAR = "from_calendar"  # External → Workmate
    BIDIRECTIONAL = "bidirectional"  # Both ways


class Integration(Base):
    """External service integrations (calendars, etc.)"""

    __tablename__ = "integrations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Integration details
    name = Column(String, nullable=False)  # User-defined name
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)
    enabled = Column(Boolean, default=True)

    # Configuration (encrypted credentials, URLs, etc.)
    config = Column(JSON, nullable=False)  # Stores URL, username, calendar_id, etc.
    credentials = Column(JSON, nullable=True)  # Encrypted OAuth tokens or passwords

    # Sync settings
    sync_direction = Column(SQLEnum(SyncDirection), default=SyncDirection.BIDIRECTIONAL)
    auto_sync = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)  # How often to sync

    # Sync status
    sync_status = Column(String, default="idle")  # idle, syncing, success, error
    last_sync_at = Column(DateTime, nullable=True)
    error_log = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="integrations")
    calendar_events = relationship("CalendarEvent", back_populates="integration", cascade="all, delete-orphan")
