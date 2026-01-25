"""
Task model
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from ..db.base import Base


class TaskStatus(str, Enum):
    """Task status enum"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(Base):
    """Task model"""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True)

    # Content
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Scheduling
    due_date = Column(DateTime, index=True)
    estimated_duration_minutes = Column(Integer)

    # Status
    status = Column(String(50), default=TaskStatus.OPEN, index=True)
    priority = Column(String(50), default=TaskPriority.MEDIUM, index=True)

    # Metadata
    amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="EUR")

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="tasks")
    document = relationship("Document", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], backref="subtasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"
