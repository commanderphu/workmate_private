"""
Database initialization utilities
"""

from sqlalchemy.orm import Session
from ..core.security import get_password_hash
from ..models import User


def init_db(db: Session) -> None:
    """Initialize database with default data"""
    print("✅ Database initialized")
