"""
Transformation metadata and result models.

Defines metadata structures for tracking transformation
progress, results, and statistics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum


class TransformationStatus(Enum):
    """Status of transformation job."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransformationMetadata:
    """
    Metadata about a transformation operation.
    
    Tracks progress, timing, and statistics for transformation jobs.
    """
    job_id: str
    status: TransformationStatus = TransformationStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    
    # Input statistics
    input_modules_count: int = 0
    input_classes_count: int = 0
    input_functions_count: int = 0
    input_variables_count: int = 0
    
    # Output statistics
    output_nodes_count: int = 0
    output_relationships_count: int = 0
    output_formats: Set[str] = field(default_factory=set)
    
    # Processing statistics
    processing_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    batch_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    
    # Detailed progress tracking
    steps_completed: List[str] = field(default_factory=list)
    steps_remaining: List[str] = field(default_factory=list)
    
    def start(self) -> None:
        """Mark transformation as started."""
        self.status = TransformationStatus.RUNNING
        self.started_at = datetime.utcnow()
        
    def complete(self) -> None:
        """Mark transformation as completed."""
        self.status = TransformationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
            
    def fail(self, error_message: str = "") -> None:
        """Mark transformation as failed."""
        self.status = TransformationStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error_message:
            self.current_step = f"FAILED: {error_message}"
            
    def update_progress(self, percentage: float, step: str = "") -> None:
        """Update progress percentage and current step."""
        self.progress_percentage = min(100.0, max(0.0, percentage))
        if step:
            self.current_step = step
            
    def add_completed_step(self, step: str) -> None:
        """Add a completed step."""
        if step not in self.steps_completed:
            self.steps_completed.append(step)
        if step in self.steps_remaining:
            self.steps_remaining.remove(step)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "input_statistics": {
                "modules": self.input_modules_count,
                "classes": self.input_classes_count,
                "functions": self.input_functions_count,
                "variables": self.input_variables_count
            },
            "output_statistics": {
                "nodes": self.output_nodes_count,
                "relationships": self.output_relationships_count,
                "formats": list(self.output_formats)
            },
            "processing_statistics": {
                "time_seconds": self.processing_time_seconds,
                "memory_peak_mb": self.memory_peak_mb,
                "batch_count": self.batch_count,
                "error_count": self.error_count,
                "warning_count": self.warning_count
            },
            "progress": {
                "steps_completed": self.steps_completed,
                "steps_remaining": self.steps_remaining
            }
        }


@dataclass
class TransformationResult:
    """
    Result of a transformation operation.
    
    Contains the generated tuples, metadata, and any errors or warnings.
    """
    job_id: str
    metadata: TransformationMetadata
    output_files: Dict[str, str] = field(default_factory=dict)  # format -> file_path
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Optional tuple data (for in-memory processing)
    tuple_data: Optional[Dict[str, Any]] = None
    
    @property
    def success(self) -> bool:
        """Check if transformation was successful."""
        return self.metadata.status == TransformationStatus.COMPLETED
        
    @property
    def has_errors(self) -> bool:
        """Check if transformation has errors."""
        return len(self.errors) > 0
        
    @property
    def has_warnings(self) -> bool:
        """Check if transformation has warnings."""
        return len(self.warnings) > 0
        
    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.metadata.error_count += 1
        
    def add_warning(self, warning: str) -> None:
        """Add a warning to the result."""
        self.warnings.append(warning)
        self.metadata.warning_count += 1
        
    def add_output_file(self, format_name: str, file_path: str) -> None:
        """Add an output file for a specific format."""
        self.output_files[format_name] = file_path
        self.metadata.output_formats.add(format_name)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "success": self.success,
            "metadata": self.metadata.to_dict(),
            "output_files": self.output_files,
            "errors": self.errors,
            "warnings": self.warnings,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings
        }