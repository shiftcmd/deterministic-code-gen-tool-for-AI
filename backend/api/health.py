"""
Health check routes for the Python Debug Tool API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def api_health_check() -> dict[str, str]:
    """API Health check endpoint for frontend."""
    return {"status": "healthy", "service": "python-debug-tool"}


@router.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"message": "Python Debug Tool API is running", "version": "0.1.0"} 