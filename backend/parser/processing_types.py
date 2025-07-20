"""
Shared processing types and classes for the parser system.

This module contains shared data structures used across the parser components
to avoid circular import issues.
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4


logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Processing strategy options."""
    THREAD_BASED = "thread_based"
    PROCESS_BASED = "process_based" 
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


@dataclass
class ProcessingMetrics:
    """Processing performance metrics."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    memory_peak: int = 0  # MB
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def duration(self) -> float:
        """Get processing duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def files_per_second(self) -> float:
        """Calculate processing speed."""
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.processed_files / duration


@dataclass
class ParsingTask:
    """Individual parsing task with metadata."""
    file_path: str
    priority: int = 0
    task_id: str = field(default_factory=lambda: str(uuid4()))
    dependencies: List[str] = field(default_factory=list)
    estimated_memory: int = 0  # MB
    start_time: Optional[float] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()


class ProgressTracker:
    """Thread-safe progress tracking with observer pattern."""
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.completed_files = 0
        self.failed_files = 0
        self.current_file = ""
        self.observers: List[Callable[[Dict[str, Any]], None]] = []
        self._lock = None
        
        # Import threading here to avoid circular imports
        import threading
        self._lock = threading.Lock()
    
    def add_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Add progress observer."""
        with self._lock:
            self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove progress observer."""
        with self._lock:
            if callback in self.observers:
                self.observers.remove(callback)
    
    def update_progress(self, completed: int = 0, failed: int = 0, current_file: str = ""):
        """Update progress and notify observers."""
        with self._lock:
            self.completed_files += completed
            self.failed_files += failed
            if current_file:
                self.current_file = current_file
            
            # Notify observers
            progress_data = {
                "total_files": self.total_files,
                "completed_files": self.completed_files,
                "failed_files": self.failed_files,
                "current_file": self.current_file,
                "percentage": (self.completed_files / max(self.total_files, 1)) * 100
            }
            
            for observer in self.observers:
                try:
                    observer(progress_data)
                except Exception as e:
                    logger.warning(f"Progress observer failed: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress data."""
        with self._lock:
            return {
                "total_files": self.total_files,
                "completed_files": self.completed_files,
                "failed_files": self.failed_files,
                "current_file": self.current_file,
                "percentage": (self.completed_files / max(self.total_files, 1)) * 100
            }
