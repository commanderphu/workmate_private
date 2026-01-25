"""
API v1 router
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .tasks import router as tasks_router
from .documents import router as documents_router

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
