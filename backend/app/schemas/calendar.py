"""
Calendar and Integration schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


# ===== CalendarEvent Schemas =====

class CalendarEventBase(BaseModel):
    """Base calendar event schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    location: Optional[str] = None


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating a calendar event"""
    task_id: Optional[uuid.UUID] = None
    external_calendar_id: Optional[uuid.UUID] = None


class CalendarEventUpdate(BaseModel):
    """Schema for updating a calendar event"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    task_id: Optional[uuid.UUID] = None


class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event response"""
    id: uuid.UUID
    user_id: uuid.UUID
    task_id: Optional[uuid.UUID]
    external_event_id: Optional[str]
    external_calendar_id: Optional[uuid.UUID]
    sync_status: str
    last_synced_at: Optional[datetime]
    conflict_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Integration Schemas =====

class IntegrationBase(BaseModel):
    """Base integration schema"""
    name: str = Field(..., min_length=1, max_length=255)
    integration_type: str = Field(..., pattern="^(caldav|google_calendar|outlook_calendar)$")
    enabled: bool = True
    sync_direction: str = Field(default="bidirectional", pattern="^(to_calendar|from_calendar|bidirectional)$")
    auto_sync: bool = True
    sync_interval_minutes: int = Field(default=15, ge=5, le=1440)


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration"""
    config: Dict[str, Any]  # URL, calendar_id, etc.
    credentials: Optional[Dict[str, Any]] = None  # Username, password, tokens


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    sync_direction: Optional[str] = Field(None, pattern="^(to_calendar|from_calendar|bidirectional)$")
    auto_sync: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None


class IntegrationResponse(IntegrationBase):
    """Schema for integration response"""
    id: uuid.UUID
    user_id: uuid.UUID
    config: Dict[str, Any]
    sync_status: str
    last_sync_at: Optional[datetime]
    error_log: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Sync Schemas =====

class SyncRequest(BaseModel):
    """Schema for manual sync request"""
    force: bool = False  # Force sync even if auto_sync is disabled


class SyncResponse(BaseModel):
    """Schema for sync response"""
    success: bool
    events_synced: int
    conflicts: int
    errors: int
    message: str
