"""
Neo4j Manager Package

Domain for managing Neo4j database versioning, backups, and restoration.
"""

from .core import BackupManager, DatabaseTracker, Neo4jService, TarballManager
from .services import BackupService
from .models import (
    BackupResult,
    RestoreResult,
    BackupMetadata,
    ServiceOperationResult,
    TarballResult,
    DatabaseVersion,
    VersionHistory,
    BackupRegistry
)

__all__ = [
    # Core components
    "BackupManager",
    "DatabaseTracker",
    "Neo4jService", 
    "TarballManager",
    
    # Services
    "BackupService",
    
    # Models
    "BackupResult",
    "RestoreResult",
    "BackupMetadata",
    "ServiceOperationResult",
    "TarballResult",
    "DatabaseVersion",
    "VersionHistory",
    "BackupRegistry"
]