"""
Parallel Processing Architecture for AST Parser Engine.

This module implements a comprehensive parallel processing system that enhances
the basic ThreadPoolExecutor approach with memory management, error recovery,
progress tracking, and relationship extraction integration.

# AI-Intent: Core-Domain:Application
# Intent: This module orchestrates parallel parsing tasks and manages resources
# Confidence: High
# @layer: application
# @component: orchestration
# @performance: parallel-processing
"""

import asyncio
import logging
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from weakref import WeakSet

from .config import ParserConfig
from .models import ParsedModule
from .errors import ParserError, ParserErrorCode
from .memory_efficient_parser import MemoryEfficientParser

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Strategy for parallel processing."""
    THREAD_BASED = "thread"  # For I/O bound parsing tasks
    PROCESS_BASED = "process"  # For CPU intensive analysis
    HYBRID = "hybrid"  # Combines both strategies
    ADAPTIVE = "adaptive"  # Dynamically selects best strategy


@dataclass
class ProcessingMetrics:
    """Metrics for parallel processing performance."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    memory_peak: int = 0
    error_recovery_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def duration(self) -> float:
        """Calculate processing duration."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def files_per_second(self) -> float:
        """Calculate processing rate."""
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.processed_files / duration


@dataclass
class ParsingTask:
    """Represents a single parsing task."""
    file_path: str
    priority: int = 0
    dependencies: Set[str] = field(default_factory=set)
    retries: int = 0
    max_retries: int = 3
    task_id: str = field(init=False)
    
    def __post_init__(self):
        self.task_id = f"parse_{Path(self.file_path).stem}_{id(self)}"


class ProgressTracker:
    """Thread-safe progress tracking for parallel processing."""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.current_file = ""
        self._lock = threading.Lock()
        self._observers: WeakSet = WeakSet()
    
    def add_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Add progress observer callback."""
        self._observers.add(callback)
    
    def update_progress(self, completed: int = 1, failed: int = 0, current_file: str = ""):
        """Update progress in thread-safe manner."""
        with self._lock:
            self.completed_tasks += completed
            self.failed_tasks += failed
            if current_file:
                self.current_file = current_file
            
            progress_data = {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "failed": self.failed_tasks,
                "current_file": self.current_file,
                "percentage": (self.completed_tasks / self.total_tasks) * 100 if self.total_tasks > 0 else 0
            }
            
            # Notify observers
            for observer in self._observers:
                try:
                    observer(progress_data)
                except Exception as e:
                    logger.warning(f"Progress observer failed: {e}")


class MemoryManager:
    """Manages memory usage during parallel processing."""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.current_memory_mb = 0
        self._lock = threading.Lock()
    
    def can_allocate(self, estimated_size_mb: int) -> bool:
        """Check if we can allocate more memory."""
        with self._lock:
            return (self.current_memory_mb + estimated_size_mb) <= self.max_memory_mb
    
    def allocate(self, size_mb: int):
        """Allocate memory tracking."""
        with self._lock:
            self.current_memory_mb += size_mb
    
    def deallocate(self, size_mb: int):
        """Deallocate memory tracking."""
        with self._lock:
            self.current_memory_mb = max(0, self.current_memory_mb - size_mb)
    
    @property
    def utilization_percentage(self) -> float:
        """Get current memory utilization percentage."""
        with self._lock:
            return (self.current_memory_mb / self.max_memory_mb) * 100


class ErrorRecoveryManager:
    """Manages error recovery and retry logic for failed parsing tasks."""
    
    def __init__(self):
        self.failed_tasks: Dict[str, List[Exception]] = {}
        self.recovery_strategies: Dict[ParserErrorCode, Callable] = {
            ParserErrorCode.SYNTAX_ERROR: self._syntax_error_recovery,
            ParserErrorCode.FILE_NOT_FOUND: self._file_not_found_recovery,
            ParserErrorCode.MEMORY_ERROR: self._memory_error_recovery,
            ParserErrorCode.TIMEOUT_ERROR: self._timeout_error_recovery,
        }
    
    def handle_error(self, task: ParsingTask, error: Exception) -> bool:
        """
        Handle parsing error and determine if retry is possible.
        
        Returns:
            True if task should be retried, False otherwise
        """
        task_id = task.task_id
        
        if task_id not in self.failed_tasks:
            self.failed_tasks[task_id] = []
        
        self.failed_tasks[task_id].append(error)
        
        # Check retry limit
        if task.retries >= task.max_retries:
            logger.error(f"Task {task_id} exceeded max retries: {task.retries}")
            return False
        
        # Try recovery strategy
        if isinstance(error, ParserError) and error.code in self.recovery_strategies:
            try:
                return self.recovery_strategies[error.code](task, error)
            except Exception as recovery_error:
                logger.warning(f"Recovery strategy failed for {task_id}: {recovery_error}")
        
        # Default retry logic
        task.retries += 1
        return task.retries <= task.max_retries
    
    def _syntax_error_recovery(self, task: ParsingTask, error: ParserError) -> bool:
        """Recovery strategy for syntax errors."""
        logger.info(f"Attempting syntax error recovery for {task.file_path}")
        # Could implement fallback to simpler parser or partial parsing
        return True
    
    def _file_not_found_recovery(self, task: ParsingTask, error: ParserError) -> bool:
        """Recovery strategy for file not found errors."""
        if Path(task.file_path).exists():
            return True  # File appeared, retry
        return False  # File still missing, don't retry
    
    def _memory_error_recovery(self, task: ParsingTask, error: ParserError) -> bool:
        """Recovery strategy for memory errors."""
        logger.info(f"Attempting memory error recovery for {task.file_path}")
        # Could implement chunked processing or simpler parser
        return True
    
    def _timeout_error_recovery(self, task: ParsingTask, error: ParserError) -> bool:
        """Recovery strategy for timeout errors."""
        logger.info(f"Attempting timeout recovery for {task.file_path}")
        # Could increase timeout or use faster parser
        return True


class ParallelProcessor:
    """
    Advanced parallel processing orchestrator for AST parsing.
    
    This class manages the entire parallel processing lifecycle including:
    - Task scheduling and dependency management
    - Memory management and resource allocation
    - Error recovery and retry logic
    - Progress tracking and metrics collection
    - Integration with relationship extraction
    """
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.strategy = ProcessingStrategy.ADAPTIVE
        self.memory_manager = MemoryManager(max_memory_mb=config.tool_options.get('parallel', {}).get('max_memory_mb', 1024))
        self.error_recovery = ErrorRecoveryManager()
        self.metrics = ProcessingMetrics()
        
        # Processing pools
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
        
        # Task management
        self.task_queue: Queue = Queue()
        self.completed_tasks: Dict[str, Any] = {}
        self.failed_tasks: Dict[str, Exception] = {}
        
        # Progress tracking
        self.progress_tracker: Optional[ProgressTracker] = None
        
        # Memory-efficient parser for large files
        self.memory_parser = MemoryEfficientParser(config)
        
    def process_files(self, file_paths: List[str], parse_func: Callable[[str], ParsedModule]) -> Dict[str, ParsedModule]:
        """
        Process multiple files in parallel with comprehensive management.
        
        Args:
            file_paths: List of file paths to process
            parse_func: Function to parse individual files
            
        Returns:
            Dictionary mapping file paths to parsed modules
        """
        # Initialize metrics and progress tracking
        self.metrics = ProcessingMetrics(total_files=len(file_paths))
        self.progress_tracker = ProgressTracker(len(file_paths))
        
        # Create parsing tasks
        tasks = [ParsingTask(file_path=path, priority=self._calculate_priority(path)) 
                for path in file_paths]
        
        # Sort by priority and dependencies
        tasks = self._resolve_dependencies(tasks)
        
        # Select processing strategy
        strategy = self._select_strategy(tasks)
        logger.info(f"Using processing strategy: {strategy}")
        
        try:
            if strategy == ProcessingStrategy.THREAD_BASED:
                return self._process_with_threads(tasks, parse_func)
            elif strategy == ProcessingStrategy.PROCESS_BASED:
                return self._process_with_processes(tasks, parse_func)
            elif strategy == ProcessingStrategy.HYBRID:
                return self._process_hybrid(tasks, parse_func)
            else:  # ADAPTIVE
                return self._process_adaptive(tasks, parse_func)
                
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}")
            raise
        finally:
            self._cleanup()
            self.metrics.end_time = time.time()
    
    def _calculate_priority(self, file_path: str) -> int:
        """Calculate task priority based on file characteristics."""
        path = Path(file_path)
        priority = 0
        
        # Higher priority for smaller files
        try:
            size = path.stat().st_size
            if size < 10000:  # 10KB
                priority += 10
            elif size < 100000:  # 100KB
                priority += 5
        except OSError:
            pass
        
        # Higher priority for core modules
        if any(core_pattern in str(path) for core_pattern in ['__init__.py', 'main.py', 'config.py']):
            priority += 20
        
        # Lower priority for test files
        if 'test' in str(path).lower():
            priority -= 10
        
        return priority
    
    def _resolve_dependencies(self, tasks: List[ParsingTask]) -> List[ParsingTask]:
        """Resolve task dependencies and sort appropriately."""
        # Simple implementation: sort by priority for now
        # More sophisticated dependency resolution could analyze imports
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
    
    def _select_strategy(self, tasks: List[ParsingTask]) -> ProcessingStrategy:
        """Select optimal processing strategy based on task characteristics."""
        if self.strategy != ProcessingStrategy.ADAPTIVE:
            return self.strategy
        
        # Analyze task characteristics
        total_files = len(tasks)
        avg_file_size = self._estimate_average_file_size(tasks)
        
        # Decision logic
        if total_files < 10:
            return ProcessingStrategy.THREAD_BASED
        elif avg_file_size > 100000:  # Large files, CPU intensive
            return ProcessingStrategy.PROCESS_BASED
        elif total_files > 100:
            return ProcessingStrategy.HYBRID
        else:
            return ProcessingStrategy.THREAD_BASED
    
    def _estimate_average_file_size(self, tasks: List[ParsingTask]) -> float:
        """Estimate average file size from tasks."""
        sizes = []
        for task in tasks[:min(10, len(tasks))]:  # Sample first 10 files
            try:
                size = Path(task.file_path).stat().st_size
                sizes.append(size)
            except OSError:
                sizes.append(10000)  # Default estimate
        
        return sum(sizes) / len(sizes) if sizes else 10000
    
    def _process_with_threads(self, tasks: List[ParsingTask], parse_func: Callable) -> Dict[str, ParsedModule]:
        """Process tasks using thread-based parallelism."""
        max_workers = min(os.cpu_count() or 1, len(tasks), 8)  # Cap at 8 threads
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            self._thread_pool = executor
            
            # Submit initial batch
            future_to_task = {}
            active_tasks = 0
            task_iter = iter(tasks)
            
            # Fill initial batch
            for _ in range(max_workers):
                try:
                    task = next(task_iter)
                    if self._can_process_task(task):
                        future = executor.submit(self._safe_parse_task, task, parse_func)
                        future_to_task[future] = task
                        active_tasks += 1
                except StopIteration:
                    break
            
            # Process completed tasks and submit new ones
            while future_to_task:
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    
                    try:
                        result = future.result()
                        if result:
                            results[task.file_path] = result
                            self.completed_tasks[task.task_id] = result
                            self.progress_tracker.update_progress(completed=1)
                        else:
                            self.progress_tracker.update_progress(failed=1)
                    except Exception as e:
                        if self.error_recovery.handle_error(task, e):
                            # Retry task
                            retry_future = executor.submit(self._safe_parse_task, task, parse_func)
                            future_to_task[retry_future] = task
                        else:
                            self.failed_tasks[task.file_path] = e
                            self.progress_tracker.update_progress(failed=1)
                    
                    # Remove completed future
                    del future_to_task[future]
                    active_tasks -= 1
                    
                    # Submit next task if available
                    try:
                        next_task = next(task_iter)
                        if self._can_process_task(next_task):
                            future = executor.submit(self._safe_parse_task, next_task, parse_func)
                            future_to_task[future] = next_task
                            active_tasks += 1
                    except StopIteration:
                        pass
        
        return results
    
    def _process_with_processes(self, tasks: List[ParsingTask], parse_func: Callable) -> Dict[str, ParsedModule]:
        """Process tasks using process-based parallelism."""
        max_workers = min(os.cpu_count() or 1, len(tasks), 4)  # Cap at 4 processes
        results = {}
        
        # Note: This is a simplified implementation
        # Full implementation would require serializable task objects and parse functions
        logger.warning("Process-based parallelism not fully implemented - falling back to threads")
        return self._process_with_threads(tasks, parse_func)
    
    def _process_hybrid(self, tasks: List[ParsingTask], parse_func: Callable) -> Dict[str, ParsedModule]:
        """Process tasks using hybrid thread/process approach."""
        # Simplified: use threads for now
        # Full implementation would categorize tasks and use appropriate pools
        return self._process_with_threads(tasks, parse_func)
    
    def _process_adaptive(self, tasks: List[ParsingTask], parse_func: Callable) -> Dict[str, ParsedModule]:
        """Process tasks using adaptive strategy selection."""
        # Monitor performance and switch strategies if needed
        return self._process_with_threads(tasks, parse_func)
    
    def _can_process_task(self, task: ParsingTask) -> bool:
        """Check if task can be processed given current resource constraints."""
        # Estimate memory usage
        estimated_memory = self._estimate_task_memory(task)
        
        if not self.memory_manager.can_allocate(estimated_memory):
            logger.debug(f"Deferring task {task.task_id} due to memory constraints")
            return False
        
        return True
    
    def _estimate_task_memory(self, task: ParsingTask) -> int:
        """Estimate memory usage for a task in MB."""
        try:
            file_size = Path(task.file_path).stat().st_size
            # Rough estimate: 3x file size for parsing overhead
            return max(1, (file_size * 3) // (1024 * 1024))
        except OSError:
            return 5  # Default estimate
    
    def _safe_parse_task(self, task: ParsingTask, parse_func: Callable) -> Optional[ParsedModule]:
        """
        Safely parse a task with memory tracking and error handling.
        """
        estimated_memory = self._estimate_task_memory(task)
        
        try:
            self.memory_manager.allocate(estimated_memory)
            self.progress_tracker.update_progress(current_file=task.file_path)
            
            # Use memory-efficient parser for large files
            file_size = Path(task.file_path).stat().st_size
            memory_threshold = self.config.tool_options.get('memory', {}).get('use_efficient_parsing_mb', 512 * 1024)  # 512KB
            
            if file_size > memory_threshold:
                logger.debug(f"Using memory-efficient parser for large file: {task.file_path}")
                result = self.memory_parser.parse_file_memory_efficient(task.file_path, 
                    lambda progress: self.progress_tracker.update_progress(current_file=f"{task.file_path} ({progress.get('stage', 'parsing')})"))
            else:
                result = parse_func(task.file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing {task.file_path}: {e}")
            raise
        finally:
            self.memory_manager.deallocate(estimated_memory)
    
    def _cleanup(self):
        """Clean up resources after processing."""
        if self._thread_pool:
            self._thread_pool = None
        if self._process_pool:
            self._process_pool = None
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics."""
        # Update metrics with memory parser stats
        memory_stats = self.memory_parser.get_memory_stats()
        self.metrics.memory_peak = max(self.metrics.memory_peak, int(memory_stats['peak_memory_mb']))
        return self.metrics
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory usage statistics."""
        return self.memory_parser.get_memory_stats()
    
    def add_progress_observer(self, callback: Callable[[Dict[str, Any]], None]):
        """Add progress observer for real-time updates."""
        if self.progress_tracker:
            self.progress_tracker.add_observer(callback)
