"""
Upload Result Models for Neo4j Uploader

Defines data models for tracking upload operations, results, and statistics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UploadResult(BaseModel):
    """Result model for Neo4j upload operations."""
    
    job_id: str = Field(..., description="Job ID for this upload operation")
    success: bool = Field(default=False, description="Whether the upload was successful")
    
    # Upload statistics
    nodes_created: int = Field(default=0, description="Number of nodes created")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    properties_set: int = Field(default=0, description="Number of properties set")
    total_commands: int = Field(default=0, description="Total number of Cypher commands")
    total_commands_executed: int = Field(default=0, description="Number of commands successfully executed")
    
    # Performance metrics
    upload_duration_seconds: float = Field(default=0.0, description="Total upload duration in seconds")
    average_command_time_ms: float = Field(default=0.0, description="Average time per command in milliseconds")
    
    # File information
    cypher_file_path: Optional[str] = Field(None, description="Path to the Cypher commands file")
    cypher_file_size_bytes: Optional[int] = Field(None, description="Size of the Cypher file in bytes")
    
    # Estimation vs actual
    estimated_nodes: Optional[int] = Field(None, description="Estimated number of nodes before upload")
    estimated_relationships: Optional[int] = Field(None, description="Estimated number of relationships before upload")
    
    # Error tracking
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    failed_commands: List[Dict[str, Any]] = Field(default_factory=list, description="Commands that failed with details")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="When the upload started")
    completed_at: Optional[datetime] = Field(None, description="When the upload completed")
    
    def add_error(self, error: str, command: Optional[str] = None) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        if command:
            self.failed_commands.append({
                "command": command[:200] + "..." if len(command) > 200 else command,
                "error": error,
                "timestamp": datetime.now().isoformat()
            })
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.total_commands_executed / self.total_commands) * 100
    
    def merge_stats(self, other: 'UploadResult') -> None:
        """Merge statistics from another upload result."""
        self.nodes_created += other.nodes_created
        self.relationships_created += other.relationships_created
        self.properties_set += other.properties_set
        self.total_commands_executed += other.total_commands_executed
        self.errors.extend(other.errors)
        self.failed_commands.extend(other.failed_commands)
    
    def merge_batch_result(self, batch: 'BatchResult') -> None:
        """Merge statistics from a batch result."""
        self.nodes_created += batch.nodes_created
        self.relationships_created += batch.relationships_created
        self.properties_set += batch.properties_set
        self.total_commands_executed += batch.commands_in_batch
        self.errors.extend(batch.errors)
        if not batch.success:
            self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "nodes_created": self.nodes_created,
            "relationships_created": self.relationships_created,
            "properties_set": self.properties_set,
            "total_commands": self.total_commands,
            "total_commands_executed": self.total_commands_executed,
            "completion_percentage": self.completion_percentage,
            "upload_duration_seconds": self.upload_duration_seconds,
            "average_command_time_ms": self.average_command_time_ms,
            "cypher_file_path": self.cypher_file_path,
            "cypher_file_size_bytes": self.cypher_file_size_bytes,
            "estimated_nodes": self.estimated_nodes,
            "estimated_relationships": self.estimated_relationships,
            "errors": self.errors,
            "error_count": len(self.errors),
            "failed_commands": self.failed_commands,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "has_errors": self.has_errors
        }


class BatchResult(BaseModel):
    """Result model for a single batch of uploads."""
    
    batch_number: int = Field(..., description="Batch sequence number")
    job_id: str = Field(..., description="Job ID for this batch")
    success: bool = Field(default=False, description="Whether the batch was successful")
    
    # Batch statistics
    commands_in_batch: int = Field(..., description="Number of commands in this batch")
    nodes_created: int = Field(default=0, description="Nodes created in this batch")
    relationships_created: int = Field(default=0, description="Relationships created in this batch")
    properties_set: int = Field(default=0, description="Properties set in this batch")
    
    # Performance
    execution_time_seconds: float = Field(default=0.0, description="Time to execute this batch")
    
    # Errors
    errors: List[str] = Field(default_factory=list, description="Errors in this batch")
    
    def add_error(self, error: str) -> None:
        """Add an error to the batch result."""
        self.errors.append(error)
        self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "batch_number": self.batch_number,
            "job_id": self.job_id,
            "success": self.success,
            "commands_in_batch": self.commands_in_batch,
            "nodes_created": self.nodes_created,
            "relationships_created": self.relationships_created,
            "properties_set": self.properties_set,
            "execution_time_seconds": self.execution_time_seconds,
            "errors": self.errors,
            "error_count": len(self.errors)
        }


class ConnectionHealth(BaseModel):
    """Model for Neo4j connection health status."""
    
    healthy: bool = Field(..., description="Whether the connection is healthy")
    last_check: datetime = Field(..., description="When the health check was performed")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    database_version: Optional[str] = Field(None, description="Neo4j database version")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "healthy": self.healthy,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "database_version": self.database_version,
            "error": self.error
        }


class ValidationResult(BaseModel):
    """Result model for Cypher file validation."""
    
    is_valid: bool = Field(..., description="Whether the file is valid")
    file_path: str = Field(..., description="Path to the validated file")
    file_size_bytes: int = Field(default=0, description="Size of the file in bytes")
    total_commands: int = Field(default=0, description="Number of Cypher commands found")
    estimated_nodes: int = Field(default=0, description="Estimated nodes to be created")
    estimated_relationships: int = Field(default=0, description="Estimated relationships to be created")
    errors: List[str] = Field(default_factory=list, description="Validation errors found")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": self.file_size_bytes / (1024 * 1024),
            "total_commands": self.total_commands,
            "estimated_nodes": self.estimated_nodes,
            "estimated_relationships": self.estimated_relationships,
            "errors": self.errors,
            "error_count": len(self.errors),
            "warnings": self.warnings,
            "warning_count": len(self.warnings)
        }