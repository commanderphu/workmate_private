"""
Workmate Private Backend API
Intelligent document and task management for ADHD
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Workmate Private API",
    description="Intelligent document and task management for ADHD",
    version="0.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint - API info"""
    return {
        "message": "Workmate Private API",
        "version": "0.1.0",
        "status": "Development"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
