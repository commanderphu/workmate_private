"""
Task schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
import uuid


class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    amount: Optional[Decimal] = None
    currency: str = "EUR"


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    document_id: Optional[uuid.UUID] = None
    parent_task_id: Optional[uuid.UUID] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(open|in_progress|done|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    amount: Optional[Decimal] = None


class TaskResponse(TaskBase):
    """Schema for task response"""
    id: uuid.UUID
    user_id: uuid.UUID
    document_id: Optional[uuid.UUID]
    parent_task_id: Optional[uuid.UUID]
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
