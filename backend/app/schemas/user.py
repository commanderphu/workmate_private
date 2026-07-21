"""
User schemas for API requests/responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    """PATCH /auth/me — all configurable user parameters"""
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    # Paperless-ngx per-user credentials
    paperless_url: Optional[str] = None
    paperless_token: Optional[str] = None
    # Notification preferences
    notifications_push_enabled: Optional[bool] = None
    notifications_email_enabled: Optional[bool] = None
    notifications_reminder_minutes: Optional[int] = None
    # UI preferences (arbitrary extra keys forwarded as-is)
    ui_preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    timezone: str
    language: str
    created_at: datetime
    last_login_at: Optional[datetime]
    ui_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
