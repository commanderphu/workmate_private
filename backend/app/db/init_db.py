"""
Database initialization utilities
"""

from sqlalchemy.orm import Session
from ..core.security import get_password_hash
from ..models import User


def init_db(db: Session) -> None:
    """Initialize database with default data"""
    # Check if we have any users
    user = db.query(User).first()
    if not user:
        # Create a default admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin"),
            full_name="Admin User",
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        db.commit()
        print("✅ Created default admin user (username: admin, password: admin)")
    else:
        print("✅ Database already initialized")
