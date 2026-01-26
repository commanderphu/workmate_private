"""
Calendar Event model
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..core.database import Base


class CalendarSyncStatus(str, enum.Enum):
    """Sync status for calendar events"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class CalendarEvent(Base):
    """Calendar events that sync with external calendars"""

    __tablename__ = "calendar_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)

    # Event details
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)
    location = Column(String, nullable=True)

    # External calendar sync
    external_event_id = Column(String, nullable=True)  # ID in external calendar
    external_calendar_id = Column(String, ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True)

    # Sync metadata
    sync_status = Column(SQLEnum(CalendarSyncStatus), default=CalendarSyncStatus.PENDING)
    last_synced_at = Column(DateTime, nullable=True)
    conflict_data = Column(JSON, nullable=True)  # Store conflict details

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    task = relationship("Task", back_populates="calendar_event")
    integration = relationship("Integration", back_populates="calendar_events")
