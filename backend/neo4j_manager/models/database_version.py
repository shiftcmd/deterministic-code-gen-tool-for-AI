"""
Database Version Tracking Models

Manages version tracking for Neo4j database instances and their backups.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .backup_metadata import BackupMetadata


class DatabaseVersion(BaseModel):
    """Model for tracking database versions."""
    
    job_id: str = Field(..., description="Job ID that created this database version")
    version_number: int = Field(..., description="Sequential version number")
    created_at: datetime = Field(default_factory=datetime.now, description="When this version was created")
    backup_path: Optional[str] = Field(None, description="Path to the backup for this version")
    is_active: bool = Field(default=False, description="Whether this is the current active version")
    
    # Metadata about the database content
    node_count: Optional[int] = Field(None, description="Number of nodes in this version")
    relationship_count: Optional[int] = Field(None, description="Number of relationships in this version")
    property_count: Optional[int] = Field(None, description="Number of properties in this version")
    
    # Source information
    source_codebase: Optional[str] = Field(None, description="Path to the codebase analyzed")
    extraction_job_id: Optional[str] = Field(None, description="Original extraction job ID")
    transformation_job_id: Optional[str] = Field(None, description="Transformation job ID")
    
    # Additional metadata
    description: Optional[str] = Field(None, description="Description of this version")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing versions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "backup_path": self.backup_path,
            "is_active": self.is_active,
            "node_count": self.node_count,
            "relationship_count": self.relationship_count,
            "property_count": self.property_count,
            "source_codebase": self.source_codebase,
            "extraction_job_id": self.extraction_job_id,
            "transformation_job_id": self.transformation_job_id,
            "description": self.description,
            "tags": self.tags
        }


class VersionHistory(BaseModel):
    """Model for tracking database version history."""
    
    versions: List[DatabaseVersion] = Field(default_factory=list, description="List of all database versions")
    current_version: Optional[int] = Field(None, description="Current active version number")
    
    def add_version(self, version: DatabaseVersion) -> None:
        """Add a new version to the history."""
        # Deactivate all existing versions
        for v in self.versions:
            v.is_active = False
        
        # Add and activate new version
        version.is_active = True
        version.version_number = self.get_next_version_number()
        self.versions.append(version)
        self.current_version = version.version_number
    
    def get_next_version_number(self) -> int:
        """Get the next available version number."""
        if not self.versions:
            return 1
        return max(v.version_number for v in self.versions) + 1
    
    def get_active_version(self) -> Optional[DatabaseVersion]:
        """Get the currently active version."""
        for version in self.versions:
            if version.is_active:
                return version
        return None
    
    def get_version_by_job_id(self, job_id: str) -> Optional[DatabaseVersion]:
        """Get a specific version by job ID."""
        for version in self.versions:
            if version.job_id == job_id:
                return version
        return None
    
    def get_version_by_number(self, version_number: int) -> Optional[DatabaseVersion]:
        """Get a specific version by version number."""
        for version in self.versions:
            if version.version_number == version_number:
                return version
        return None
    
    def list_versions(self, limit: Optional[int] = None) -> List[DatabaseVersion]:
        """List versions, optionally limited to most recent."""
        sorted_versions = sorted(self.versions, key=lambda v: v.created_at, reverse=True)
        if limit:
            return sorted_versions[:limit]
        return sorted_versions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "versions": [v.to_dict() for v in self.versions],
            "current_version": self.current_version,
            "total_versions": len(self.versions)
        }


class BackupRegistry(BaseModel):
    """Registry for tracking all backups."""
    
    backups: Dict[str, Any] = Field(default_factory=dict, description="Mapping of job_id to backup metadata")
    
    def register_backup(self, metadata) -> None:
        """Register a new backup."""
        self.backups[metadata.job_id] = metadata
    
    def get_backup(self, job_id: str):
        """Get backup metadata by job ID."""
        return self.backups.get(job_id)
    
    def list_backups(self, 
                    include_missing: bool = False,
                    max_age_days: Optional[int] = None) -> List[Any]:
        """List all backups with optional filtering."""
        backups = list(self.backups.values())
        
        # Filter out missing backups if requested
        if not include_missing:
            backups = [b for b in backups if b.exists()]
        
        # Filter by age if specified
        if max_age_days is not None:
            backups = [b for b in backups if b.age_days <= max_age_days]
        
        # Sort by creation date (newest first)
        return sorted(backups, key=lambda b: b.created_at, reverse=True)
    
    def get_total_size_mb(self) -> float:
        """Get total size of all backups in MB."""
        return sum(b.size_mb for b in self.backups.values() if b.exists())
    
    def cleanup_missing(self) -> List[str]:
        """Remove entries for backups that no longer exist."""
        removed = []
        for job_id, backup in list(self.backups.items()):
            if not backup.exists():
                del self.backups[job_id]
                removed.append(job_id)
        return removed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "backups": {job_id: backup.to_dict() for job_id, backup in self.backups.items()},
            "total_backups": len(self.backups),
            "total_size_mb": self.get_total_size_mb()
        }