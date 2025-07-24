"""
Progress reporting service for transformation operations.

Extends the existing communication infrastructure to provide
transformation-specific progress reporting and UI integration.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, List

from ..models.metadata import TransformationMetadata, TransformationStatus

logger = logging.getLogger(__name__)


class ProgressService:
    """Handles progress reporting for transformation operations."""
    
    def __init__(self, job_id: str, orchestrator_url: Optional[str] = None):
        """
        Initialize the progress service.
        
        Args:
            job_id: Unique identifier for this transformation job
            orchestrator_url: Base URL of the orchestrator API
        """
        self.job_id = job_id
        self.orchestrator_url = orchestrator_url or os.getenv(
            "ORCHESTRATOR_URL", 
            "http://localhost:8000"
        )
        # Note: HTTP requests disabled for testing - would use requests session in production
        self.metadata = TransformationMetadata(job_id=job_id)
        
    def start_transformation(self, input_stats: Dict[str, int]) -> bool:
        """
        Report transformation start.
        
        Args:
            input_stats: Statistics about input data (modules, classes, etc.)
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.start()
        self.metadata.input_modules_count = input_stats.get("modules", 0)
        self.metadata.input_classes_count = input_stats.get("classes", 0)
        self.metadata.input_functions_count = input_stats.get("functions", 0)
        self.metadata.input_variables_count = input_stats.get("variables", 0)
        
        return self._report_status(
            phase="transformation",
            status="started",
            message="Transformation started",
            metadata={"input_statistics": input_stats}
        )
    
    def report_progress(
        self,
        current: int,
        total: int,
        step: str = "",
        message: Optional[str] = None
    ) -> bool:
        """
        Report transformation progress.
        
        Args:
            current: Current item number
            total: Total number of items
            step: Current processing step
            message: Optional progress message
            
        Returns:
            True if reported successfully, False otherwise
        """
        progress = (current / total * 100) if total > 0 else 0
        self.metadata.update_progress(progress, step)
        
        msg = message or f"Processing {current}/{total} items"
        
        return self._report_status(
            phase="transformation",
            status="in_progress",
            message=msg,
            progress=progress,
            metadata={
                "current": current,
                "total": total,
                "step": step
            }
        )
    
    def report_step_completed(self, step: str) -> bool:
        """
        Report completion of a transformation step.
        
        Args:
            step: Name of the completed step
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.add_completed_step(step)
        
        return self._report_status(
            phase="transformation",
            status="step_completed",
            message=f"Completed step: {step}",
            metadata={"completed_step": step}
        )
    
    def report_batch_processed(
        self,
        batch_number: int,
        tuples_generated: int,
        processing_time: float
    ) -> bool:
        """
        Report completion of a batch.
        
        Args:
            batch_number: Batch sequence number
            tuples_generated: Number of tuples generated in this batch
            processing_time: Time taken to process this batch
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.batch_count += 1
        self.metadata.output_nodes_count += tuples_generated
        
        return self._report_status(
            phase="transformation",
            status="batch_completed",
            message=f"Completed batch {batch_number}",
            metadata={
                "batch_number": batch_number,
                "tuples_generated": tuples_generated,
                "processing_time": processing_time,
                "total_batches": self.metadata.batch_count
            }
        )
    
    def report_validation_results(
        self,
        validation_passed: bool,
        errors: List[str],
        warnings: List[str]
    ) -> bool:
        """
        Report validation results.
        
        Args:
            validation_passed: Whether validation passed
            errors: List of validation errors
            warnings: List of validation warnings
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.error_count += len(errors)
        self.metadata.warning_count += len(warnings)
        
        status = "validation_passed" if validation_passed else "validation_failed"
        message = "Validation passed" if validation_passed else f"Validation failed with {len(errors)} errors"
        
        return self._report_status(
            phase="transformation",
            status=status,
            message=message,
            metadata={
                "validation_passed": validation_passed,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors[:10],  # First 10 errors for brevity
                "warnings": warnings[:10]  # First 10 warnings for brevity
            }
        )
    
    def complete_transformation(
        self,
        output_files: Dict[str, str],
        final_stats: Dict[str, int]
    ) -> bool:
        """
        Report transformation completion.
        
        Args:
            output_files: Dictionary of format -> file_path
            final_stats: Final statistics about generated output
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.complete()
        self.metadata.output_nodes_count = final_stats.get("nodes", 0)
        self.metadata.output_relationships_count = final_stats.get("relationships", 0)
        self.metadata.output_formats = set(output_files.keys())
        
        return self._report_status(
            phase="transformation",
            status="completed",
            message="Transformation completed successfully",
            metadata={
                "output_files": output_files,
                "final_statistics": final_stats,
                "processing_time": self.metadata.processing_time_seconds
            }
        )
    
    def report_error(self, error_message: str, error_details: Optional[Dict] = None) -> bool:
        """
        Report transformation error.
        
        Args:
            error_message: Error message
            error_details: Optional additional error details
            
        Returns:
            True if reported successfully, False otherwise
        """
        self.metadata.fail(error_message)
        
        return self._report_status(
            phase="transformation",
            status="error",
            message=f"Transformation failed: {error_message}",
            metadata={
                "error_message": error_message,
                "error_details": error_details or {}
            }
        )
    
    def get_metadata(self) -> TransformationMetadata:
        """Get current transformation metadata."""
        return self.metadata
    
    def _report_status(
        self,
        phase: str,
        status: str,
        message: str,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Internal method to report status to orchestrator.
        
        Args:
            phase: Current phase
            status: Status of the phase
            message: Human-readable status message
            progress: Optional progress percentage (0-100)
            metadata: Optional additional metadata
            
        Returns:
            True if status was reported successfully, False otherwise
        """
        update = {
            "job_id": self.job_id,
            "phase": phase,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "progress": progress or self.metadata.progress_percentage,
            "metadata": {
                **(metadata or {}),
                "transformation_metadata": self.metadata.to_dict()
            }
        }
        
        try:
            # For testing - just write to local file
            # In production, this would send HTTP requests to orchestrator
            logger.debug(f"Status report: {status} - {message}")
            self._write_local_status(update)
            return True
            
        except Exception as e:
            # Log but don't fail - transformation should continue even if reporting fails
            logger.warning(f"Failed to report status: {e}")
            return False
    
    def _write_local_status(self, update: Dict[str, Any]) -> None:
        """Write status update to local file as fallback."""
        status_file = f"transformation_status_{self.job_id}.json"
        try:
            # Read existing status if available
            existing = []
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    existing = json.load(f)
                    
            # Append new update
            existing.append(update)
            
            # Write back
            with open(status_file, 'w') as f:
                json.dump(existing, f, indent=2)
                
            logger.debug(f"Wrote status to local file: {status_file}")
                
        except Exception as e:
            logger.error(f"Failed to write local status file: {e}")


class NullProgressService(ProgressService):
    """A no-op progress service for when orchestrator communication is disabled."""
    
    def __init__(self, job_id: str = "local"):
        """Initialize null progress service."""
        self.job_id = job_id
        self.metadata = TransformationMetadata(job_id=job_id)
        
    def _report_status(self, *args, **kwargs) -> bool:
        """No-op status report."""
        return True