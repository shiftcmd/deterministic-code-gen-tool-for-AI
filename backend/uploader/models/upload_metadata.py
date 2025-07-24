"""
Upload Metadata Models for Neo4j Uploader

Defines metadata models for tracking upload operations and progress.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class UploadPhase(str, Enum):
    """Phases of the upload process."""
    VALIDATION = "validation"
    BACKUP = "backup"
    CLEARING = "clearing"
    UPLOADING = "uploading"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadStatus(str, Enum):
    """Status of the upload operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UploadMetadata(BaseModel):
    """Metadata for tracking upload operations."""
    
    job_id: str = Field(..., description="Job ID for this upload")
    phase: UploadPhase = Field(default=UploadPhase.VALIDATION, description="Current phase of upload")
    status: UploadStatus = Field(default=UploadStatus.PENDING, description="Current status")
    
    # Source information
    source_job_id: str = Field(..., description="Job ID from Phase 2 transformation")
    cypher_file_path: str = Field(..., description="Path to Cypher commands file")
    tuples_file_path: Optional[str] = Field(None, description="Path to tuples JSON file")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, description="Overall progress percentage")
    current_batch: int = Field(default=0, description="Current batch being processed")
    total_batches: int = Field(default=0, description="Total number of batches")
    
    # Timing information
    started_at: Optional[datetime] = Field(None, description="When upload started")
    phase_started_at: Optional[datetime] = Field(None, description="When current phase started")
    completed_at: Optional[datetime] = Field(None, description="When upload completed")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Phase durations
    validation_duration_seconds: Optional[float] = Field(None, description="Time spent in validation")
    backup_duration_seconds: Optional[float] = Field(None, description="Time spent creating backup")
    clearing_duration_seconds: Optional[float] = Field(None, description="Time spent clearing database")
    upload_duration_seconds: Optional[float] = Field(None, description="Time spent uploading")
    verification_duration_seconds: Optional[float] = Field(None, description="Time spent verifying")
    
    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors by phase")
    warnings: List[str] = Field(default_factory=list, description="Warnings encountered")
    
    # Configuration
    batch_size: int = Field(default=100, description="Batch size for uploads")
    validate_before_upload: bool = Field(default=True, description="Whether to validate before upload")
    create_backup: bool = Field(default=True, description="Whether to create backup before upload")
    clear_database: bool = Field(default=True, description="Whether to clear database before upload")
    
    def update_phase(self, phase: UploadPhase) -> None:
        """Update the current phase and track timing."""
        # Complete previous phase timing
        if self.phase_started_at:
            duration = (datetime.now() - self.phase_started_at).total_seconds()
            if self.phase == UploadPhase.VALIDATION:
                self.validation_duration_seconds = duration
            elif self.phase == UploadPhase.BACKUP:
                self.backup_duration_seconds = duration
            elif self.phase == UploadPhase.CLEARING:
                self.clearing_duration_seconds = duration
            elif self.phase == UploadPhase.UPLOADING:
                self.upload_duration_seconds = duration
            elif self.phase == UploadPhase.VERIFICATION:
                self.verification_duration_seconds = duration
        
        # Update phase
        self.phase = phase
        self.phase_started_at = datetime.now()
    
    def add_error(self, phase: str, error: str) -> None:
        """Add an error for a specific phase."""
        self.errors.append({
            "phase": phase,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)
    
    def calculate_progress(self) -> float:
        """Calculate overall progress based on phase and batch progress."""
        phase_weights = {
            UploadPhase.VALIDATION: 5,
            UploadPhase.BACKUP: 10,
            UploadPhase.CLEARING: 5,
            UploadPhase.UPLOADING: 75,
            UploadPhase.VERIFICATION: 5,
            UploadPhase.COMPLETED: 100
        }
        
        base_progress = sum(phase_weights[p] for p in phase_weights if list(phase_weights.keys()).index(p) < list(phase_weights.keys()).index(self.phase))
        
        if self.phase == UploadPhase.UPLOADING and self.total_batches > 0:
            upload_progress = (self.current_batch / self.total_batches) * phase_weights[UploadPhase.UPLOADING]
            return base_progress + upload_progress
        
        return float(base_progress)
    
    def estimate_completion_time(self) -> Optional[datetime]:
        """Estimate completion time based on current progress."""
        if not self.started_at or self.progress_percentage == 0:
            return None
        
        elapsed = (datetime.now() - self.started_at).total_seconds()
        if self.progress_percentage > 0:
            total_estimated = elapsed / (self.progress_percentage / 100)
            remaining = total_estimated - elapsed
            return datetime.now() + timedelta(seconds=remaining)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "phase": self.phase.value,
            "status": self.status.value,
            "source_job_id": self.source_job_id,
            "cypher_file_path": self.cypher_file_path,
            "tuples_file_path": self.tuples_file_path,
            "progress_percentage": self.calculate_progress(),
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "phase_started_at": self.phase_started_at.isoformat() if self.phase_started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion": self.estimate_completion_time().isoformat() if self.estimate_completion_time() else None,
            "validation_duration_seconds": self.validation_duration_seconds,
            "backup_duration_seconds": self.backup_duration_seconds,
            "clearing_duration_seconds": self.clearing_duration_seconds,
            "upload_duration_seconds": self.upload_duration_seconds,
            "verification_duration_seconds": self.verification_duration_seconds,
            "errors": self.errors,
            "error_count": len(self.errors),
            "warnings": self.warnings,
            "warning_count": len(self.warnings),
            "batch_size": self.batch_size,
            "validate_before_upload": self.validate_before_upload,
            "create_backup": self.create_backup,
            "clear_database": self.clear_database
        }


from datetime import timedelta


class UploadProgress(BaseModel):
    """Model for tracking real-time upload progress."""
    
    job_id: str = Field(..., description="Job ID for this upload")
    phase: UploadPhase = Field(..., description="Current phase")
    
    # Command progress
    total_commands: int = Field(default=0, description="Total commands to execute")
    completed_commands: int = Field(default=0, description="Commands completed")
    failed_commands: int = Field(default=0, description="Commands failed")
    
    # Batch progress
    current_batch: int = Field(default=0, description="Current batch number")
    total_batches: int = Field(default=0, description="Total number of batches")
    current_batch_size: int = Field(default=0, description="Size of current batch")
    
    # Statistics
    nodes_created: int = Field(default=0, description="Total nodes created so far")
    relationships_created: int = Field(default=0, description="Total relationships created so far")
    properties_set: int = Field(default=0, description="Total properties set so far")
    
    # Performance metrics
    commands_per_second: float = Field(default=0.0, description="Average commands per second")
    estimated_time_remaining_seconds: Optional[float] = Field(None, description="Estimated time remaining")
    
    # Last update
    last_updated: datetime = Field(default_factory=datetime.now, description="Last progress update")
    
    def update(self, 
               completed_commands: Optional[int] = None,
               nodes_created: Optional[int] = None,
               relationships_created: Optional[int] = None) -> None:
        """Update progress metrics."""
        if completed_commands is not None:
            self.completed_commands = completed_commands
        if nodes_created is not None:
            self.nodes_created = nodes_created
        if relationships_created is not None:
            self.relationships_created = relationships_created
        
        self.last_updated = datetime.now()
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.completed_commands / self.total_commands) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if upload is complete."""
        return self.completed_commands >= self.total_commands
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "phase": self.phase.value,
            "total_commands": self.total_commands,
            "completed_commands": self.completed_commands,
            "failed_commands": self.failed_commands,
            "progress_percentage": self.progress_percentage,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "current_batch_size": self.current_batch_size,
            "nodes_created": self.nodes_created,
            "relationships_created": self.relationships_created,
            "properties_set": self.properties_set,
            "commands_per_second": self.commands_per_second,
            "estimated_time_remaining_seconds": self.estimated_time_remaining_seconds,
            "is_complete": self.is_complete,
            "last_updated": self.last_updated.isoformat()
        }