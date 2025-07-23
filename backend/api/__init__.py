"""
API Routes module for Python Debug Tool.

This module organizes API endpoints into logical routers for better maintainability.
"""

from .files import router as files_router
from .analysis import router as analysis_router
from .runs import router as runs_router
from .health import router as health_router
from .ide import router as ide_router

__all__ = [
    "files_router",
    "analysis_router", 
    "runs_router",
    "health_router",
    "ide_router",
] 