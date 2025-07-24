"""
Communication module for reporting status updates to the orchestrator.

This module provides the StatusReporter class that parsers use to send
real-time updates about their progress to the central orchestrator.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
import requests
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


class StatusReporter:
    """Reports parser status updates to the orchestrator."""
    
    def __init__(self, job_id: str, orchestrator_url: Optional[str] = None):
        """
        Initialize the status reporter.
        
        Args:
            job_id: Unique identifier for this parsing job
            orchestrator_url: Base URL of the orchestrator API
        """
        self.job_id = job_id
        self.orchestrator_url = orchestrator_url or os.getenv(
            "ORCHESTRATOR_URL", 
            "http://localhost:8000"
        )
        self.session = requests.Session()
        
    def report_status(
        self,
        phase: str,
        status: str,
        message: str,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Report a status update to the orchestrator.
        
        Args:
            phase: Current phase (extraction, transformation, loading)
            status: Status of the phase (started, parsing, completed, error)
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
            "progress": progress,
            "metadata": metadata or {}
        }
        
        try:
            # Try to send to orchestrator
            endpoint = urljoin(self.orchestrator_url, f"/v1/jobs/{self.job_id}/status")
            response = self.session.post(
                endpoint,
                json=update,
                timeout=5  # Don't block parsing on network issues
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            # Log but don't fail - parsing should continue even if reporting fails
            logger.warning(f"Failed to report status to orchestrator: {e}")
            
            # Fallback: write to local status file
            self._write_local_status(update)
            return False
            
    def report_file_processing(
        self,
        file_path: str,
        status: str,
        error: Optional[str] = None
    ) -> bool:
        """
        Report the processing status of a specific file.
        
        Args:
            file_path: Path to the file being processed
            status: Status (started, completed, error)
            error: Optional error message if status is error
            
        Returns:
            True if status was reported successfully, False otherwise
        """
        metadata = {
            "file_path": file_path,
            "file_status": status
        }
        if error:
            metadata["error"] = error
            
        return self.report_status(
            phase="extraction",
            status="processing_file",
            message=f"Processing {file_path}: {status}",
            metadata=metadata
        )
        
    def report_progress(
        self,
        current: int,
        total: int,
        message: Optional[str] = None
    ) -> bool:
        """
        Report progress as a percentage.
        
        Args:
            current: Current item number
            total: Total number of items
            message: Optional progress message
            
        Returns:
            True if status was reported successfully, False otherwise
        """
        progress = (current / total * 100) if total > 0 else 0
        msg = message or f"Processing {current}/{total} items"
        
        return self.report_status(
            phase="extraction",
            status="in_progress",
            message=msg,
            progress=progress,
            metadata={
                "current": current,
                "total": total
            }
        )
        
    def _write_local_status(self, update: Dict[str, Any]) -> None:
        """Write status update to local file as fallback."""
        status_file = f"extraction_status_{self.job_id}.json"
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
                
        except Exception as e:
            logger.error(f"Failed to write local status file: {e}")


class NullStatusReporter(StatusReporter):
    """A no-op status reporter for when orchestrator communication is disabled."""
    
    def __init__(self, job_id: str = "local"):
        """Initialize null reporter."""
        self.job_id = job_id
        
    def report_status(self, *args, **kwargs) -> bool:
        """No-op status report."""
        return True
        
    def report_file_processing(self, *args, **kwargs) -> bool:
        """No-op file processing report."""
        return True
        
    def report_progress(self, *args, **kwargs) -> bool:
        """No-op progress report."""
        return True