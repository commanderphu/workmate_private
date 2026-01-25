"""
SQLAlchemy base configuration
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from typing import Any

# Base class for all models
Base = declarative_base()


class BaseModel(DeclarativeBase):
    """Base model with common attributes"""
    __abstract__ = True
