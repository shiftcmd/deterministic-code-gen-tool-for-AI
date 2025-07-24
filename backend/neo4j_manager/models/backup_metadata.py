"""
Backup Metadata Models for Neo4j Manager

Defines data models for backup operations, results, and metadata tracking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field


class BackupResult(BaseModel):
    """Result model for backup operations."""
    
    job_id: str = Field(..., description="Job ID associated with this backup")
    success: bool = Field(default=False, description="Whether the backup was successful")
    backup_path: Optional[str] = Field(None, description="Path to the backup file")
    backup_size_bytes: Optional[int] = Field(None, description="Size of backup in bytes")
    backup_duration_seconds: Optional[float] = Field(None, description="Time taken to create backup")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp of backup creation")
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)
        self.success = False
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def size_mb(self) -> float:
        """Get backup size in megabytes."""
        if self.backup_size_bytes:
            return self.backup_size_bytes / (1024 * 1024)
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "backup_path": self.backup_path,
            "backup_size_bytes": self.backup_size_bytes,
            "backup_size_mb": self.size_mb,
            "backup_duration_seconds": self.backup_duration_seconds,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "has_errors": self.has_errors
        }


class RestoreResult(BaseModel):
    """Result model for restore operations."""
    
    job_id: str = Field(..., description="Job ID for the backup being restored")
    success: bool = Field(default=False, description="Whether the restore was successful")
    backup_path: Optional[str] = Field(None, description="Path to the backup file restored from")
    restore_duration_seconds: Optional[float] = Field(None, description="Time taken to restore")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    restored_at: datetime = Field(default_factory=datetime.now, description="Timestamp of restore")
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)
        self.success = False
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "backup_path": self.backup_path,
            "restore_duration_seconds": self.restore_duration_seconds,
            "errors": self.errors,
            "restored_at": self.restored_at.isoformat(),
            "has_errors": self.has_errors
        }


class BackupMetadata(BaseModel):
    """Metadata for a database backup."""
    
    job_id: str = Field(..., description="Job ID associated with this backup")
    backup_path: str = Field(..., description="Full path to the backup file")
    created_at: datetime = Field(default_factory=datetime.now, description="When the backup was created")
    size_bytes: int = Field(..., description="Size of the backup file in bytes")
    description: Optional[str] = Field(None, description="Optional description of the backup")
    neo4j_version: Optional[str] = Field(None, description="Neo4j version at backup time")
    node_count: Optional[int] = Field(None, description="Number of nodes in the backup")
    relationship_count: Optional[int] = Field(None, description="Number of relationships in the backup")
    
    @property
    def size_mb(self) -> float:
        """Get backup size in megabytes."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def age_days(self) -> int:
        """Get age of backup in days."""
        return (datetime.now() - self.created_at).days
    
    def exists(self) -> bool:
        """Check if the backup file still exists."""
        return Path(self.backup_path).exists()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "backup_path": self.backup_path,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "size_mb": self.size_mb,
            "description": self.description,
            "neo4j_version": self.neo4j_version,
            "node_count": self.node_count,
            "relationship_count": self.relationship_count,
            "age_days": self.age_days,
            "exists": self.exists()
        }


class ServiceOperationResult(BaseModel):
    """Result model for Neo4j service operations."""
    
    operation: str = Field(..., description="Operation performed (start, stop, restart)")
    success: bool = Field(default=False, description="Whether the operation was successful")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    duration_seconds: Optional[float] = Field(None, description="Time taken for the operation")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "operation": self.operation,
            "success": self.success,
            "error": self.error,
            "duration_seconds": self.duration_seconds
        }


class TarballResult(BaseModel):
    """Result model for tarball operations."""
    
    operation: str = Field(..., description="Operation performed (create, extract)")
    success: bool = Field(default=False, description="Whether the operation was successful")
    source_path: Optional[str] = Field(None, description="Source path for the operation")
    target_path: Optional[str] = Field(None, description="Target path for the operation")
    size_bytes: Optional[int] = Field(None, description="Size of the tarball in bytes")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "operation": self.operation,
            "success": self.success,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "size_bytes": self.size_bytes,
            "error": self.error
        }