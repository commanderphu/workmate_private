#!/usr/bin/env python3
"""
Initialize database script
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parents[1]))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.init_db import init_db
from app.models import User, Document, Task, File, Reminder, Session


def init() -> None:
    """Initialize database"""
    print("🚀 Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✅ Database tables created")

    # Initialize with default data
    print("🔧 Initializing default data...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    init()
