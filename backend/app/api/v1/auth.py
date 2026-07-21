"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ...db.session import get_db
from ...schemas import UserCreate, UserResponse, UserSettingsUpdate, UserLogin, Token
from ...models import User
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token
    """
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()

    # Verify user and password
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile and all configurable parameters"""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.timezone is not None:
        current_user.timezone = data.timezone
    if data.language is not None:
        current_user.language = data.language

    # Merge ui_preferences
    prefs = dict(current_user.ui_preferences or {})
    if data.paperless_url is not None:
        prefs["paperless_url"] = data.paperless_url
    if data.paperless_token is not None:
        prefs["paperless_token"] = data.paperless_token
    if data.ui_preferences:
        prefs.update(data.ui_preferences)
    current_user.ui_preferences = prefs

    # Merge notification_preferences
    notif = dict(current_user.notification_preferences or {})
    if data.notifications_push_enabled is not None:
        notif["push_enabled"] = data.notifications_push_enabled
    if data.notifications_email_enabled is not None:
        notif["email_enabled"] = data.notifications_email_enabled
    if data.notifications_reminder_minutes is not None:
        notif["reminder_minutes"] = data.notifications_reminder_minutes
    current_user.notification_preferences = notif

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
