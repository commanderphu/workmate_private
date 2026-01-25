"""
Workmate Private Backend API
Intelligent document and task management for ADHD
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from .core.config import settings
from .api.v1 import api_router

START_TIME = time.time()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent document and task management for ADHD",
    version=settings.VERSION,
    debug=settings.DEBUG,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """Root endpoint - API info"""
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "Development" if settings.DEBUG else "Production",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "status": "healthy",
        "uptime_seconds": uptime_seconds,
        "environment": settings.ENVIRONMENT,
    }
