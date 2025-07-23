"""
Main FastAPI application entry point.
"""

import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from api import (
    health_router,
    files_router,
    analysis_router,
    runs_router,
    ide_router
)

# Get application settings
settings = get_settings()

app = FastAPI(
    title="Python Debug Tool API",
    description="A comprehensive debugging and analysis utility for large Python projects",  # noqa: E501
    version="0.1.0",
    debug=settings.is_development,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,  # ✅ From config.py
    allow_credentials=True,                      # ✅ Allows cookies/auth
    allow_methods=["*"],                         # ✅ Allows all HTTP methods
    allow_headers=["*"],                         # ✅ Allows all headers
)

# Include routers
app.include_router(health_router)
app.include_router(files_router)
app.include_router(analysis_router)
app.include_router(runs_router)
app.include_router(ide_router)

# Root health check endpoint (not prefixed)
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "python-debug-tool"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",  # Use string import for reload to work
        host="0.0.0.0", 
        port=8080, 
        reload=False,  # Disable reload to avoid issues
        log_level="info"
    )
