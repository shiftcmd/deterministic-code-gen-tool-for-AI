"""
Orchestrator domain for the AST parsing pipeline.

This package contains the FastAPI-based orchestration service
that manages the entire multi-phase pipeline.
"""

from .main import app, OrchestrationService

__all__ = [
    'app',
    'OrchestrationService'
]