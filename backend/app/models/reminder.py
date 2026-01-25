"""
Reminder model
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from ..db.base import Base


class ReminderSeverity(str, Enum):
    """Reminder severity levels"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"


class ReminderStatus(str, Enum):
    """Reminder status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Reminder(Base):
    """Reminder model"""

    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scheduling
    trigger_at = Column(DateTime, nullable=False, index=True)
    severity = Column(String(50), nullable=False)

    # Channels (stored as JSON array)
    channels = Column(JSON, default=[])  # ["push", "email", "sms"]

    # Status
    status = Column(String(50), default=ReminderStatus.PENDING, index=True)
    sent_at = Column(DateTime)
    error_message = Column(Text)

    # User Action
    acknowledged_at = Column(DateTime)
    snoozed_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder {self.severity} at {self.trigger_at}>"
