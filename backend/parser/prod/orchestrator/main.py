#!/usr/bin/env python
"""
Main Orchestrator Service with FastAPI.

This module implements the central orchestration service that manages
the entire three-phase pipeline (extraction, transformation, loading)
and exposes a RESTful API for control and monitoring.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Enumeration of job statuses."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSFORMING = "transforming"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """Request model for starting analysis."""
    codebase_path: str = Field(..., description="Path to the codebase to analyze")
    neo4j_uri: Optional[str] = Field(None, description="Neo4j connection URI")
    neo4j_user: Optional[str] = Field(None, description="Neo4j username")
    neo4j_password: Optional[str] = Field(None, description="Neo4j password")


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: JobStatus
    phase: str
    progress: Optional[float] = None
    message: str
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class JobResultsResponse(BaseModel):
    """Response model for job results."""
    job_id: str
    status: JobStatus
    extraction_output: Optional[str] = None
    cypher_commands: Optional[str] = None
    tuples_output: Optional[str] = None
    loader_output: Optional[str] = None
    # Phase 3 outputs
    backup_result: Optional[str] = None
    upload_result: Optional[str] = None
    neo4j_stats: Optional[str] = None
    metrics: Dict[str, Any] = {}


class Job:
    """Represents a pipeline job."""
    
    def __init__(self, job_id: str, codebase_path: str):
        self.job_id = job_id
        self.codebase_path = codebase_path
        self.status = JobStatus.PENDING
        self.phase = "initialization"
        self.progress = 0.0
        self.message = "Job created"
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.completed_at = None
        self.error = None
        self.metadata = {}
        
        # Output files
        self.extraction_output = None
        self.cypher_commands = None
        self.tuples_output = None
        self.loader_output = None
        
        # Phase 3 output files
        self.backup_result = None    # Path to backup result file
        self.upload_result = None    # Path to upload result file
        self.neo4j_stats = None      # Upload statistics
        
        # Metrics
        self.metrics = {}


class OrchestrationService:
    """
    Central service that manages the multi-phase pipeline.
    
    This service coordinates the execution of extractor, transformer,
    and loader domains in sequence.
    """
    
    def __init__(self):
        """Initialize the orchestration service."""
        self.jobs: Dict[str, Job] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Get base directory
        self.base_dir = Path(__file__).parent.parent
        self.extractor_dir = self.base_dir / "extractor"
        self.transformer_dir = self.base_dir / "transformer"
        self.loader_dir = self.base_dir / "loader"
        
        # Phase 3 directories (go up to backend level)
        self.backend_dir = self.base_dir.parent.parent
        self.neo4j_manager_dir = self.backend_dir / "neo4j_manager"
        self.uploader_dir = self.backend_dir / "uploader"
        
    def create_job(self, codebase_path: str) -> str:
        """
        Create a new analysis job.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id, codebase_path)
        self.jobs[job_id] = job
        
        logger.info(f"Created job {job_id} for codebase: {codebase_path}")
        return job_id
        
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)
        
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        phase: str,
        message: str,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update job status."""
        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Attempted to update non-existent job: {job_id}")
            return
            
        job.status = status
        job.phase = phase
        job.message = message
        job.updated_at = datetime.utcnow()
        
        if progress is not None:
            job.progress = progress
        if error:
            job.error = error
        if metadata:
            job.metadata.update(metadata)
            
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.utcnow()
            
        logger.info(f"Job {job_id} status updated: {phase} - {status} - {message}")
        
    async def run_pipeline(self, job_id: str) -> None:
        """
        Run the complete pipeline for a job.
        
        This method orchestrates the three phases:
        1. Extraction
        2. Transformation
        3. Loading
        """
        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
            
        try:
            # Phase 1: Extraction
            self.update_job_status(
                job_id,
                JobStatus.EXTRACTING,
                "extraction",
                "Starting code extraction"
            )
            
            extraction_output = await self._run_extractor(job)
            job.extraction_output = extraction_output
            
            # Phase 2: Transformation
            self.update_job_status(
                job_id,
                JobStatus.TRANSFORMING,
                "transformation",
                "Transforming to Cypher commands"
            )
            
            cypher_commands = await self._run_transformer(job)
            job.cypher_commands = cypher_commands
            
            # Phase 3a: Backup current database
            self.update_job_status(
                job_id,
                JobStatus.LOADING,
                "backup",
                "Creating database backup"
            )
            
            backup_result = await self._run_neo4j_backup(job)
            job.backup_result = backup_result
            
            # Phase 3b: Upload to Neo4j
            self.update_job_status(
                job_id,
                JobStatus.LOADING,
                "loading",
                "Uploading to Neo4j database"
            )
            
            upload_result = await self._run_uploader(job)
            job.upload_result = upload_result
            job.loader_output = upload_result  # For backward compatibility
            
            # Mark as completed
            self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                "completed",
                "Pipeline completed successfully",
                progress=100.0
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed for job {job_id}: {e}")
            self.update_job_status(
                job_id,
                JobStatus.FAILED,
                job.phase,
                "Pipeline failed",
                error=str(e)
            )
            
    async def _run_extractor(self, job: Job) -> str:
        """Run the extractor phase."""
        output_file = f"extraction_output_{job.job_id}.json"
        
        cmd = [
            sys.executable,
            str(self.extractor_dir / "main.py"),
            "--path", job.codebase_path,
            "--job-id", job.job_id,
            "--output", output_file
        ]
        
        logger.info(f"Running extractor: {' '.join(cmd)}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            subprocess.run,
            cmd,
            subprocess.PIPE,
            subprocess.PIPE,
            True  # capture_output
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Extractor failed: {result.stderr.decode()}")
            
        return output_file
        
    async def _run_transformer(self, job: Job) -> str:
        """Run the transformer phase."""
        output_file = f"cypher_commands_{job.job_id}.cypher"
        
        cmd = [
            sys.executable,
            str(self.transformer_dir / "main.py"),
            "--input", job.extraction_output,
            "--job-id", job.job_id,
            "--output", output_file
        ]
        
        logger.info(f"Running transformer: {' '.join(cmd)}")
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            subprocess.run,
            cmd,
            subprocess.PIPE,
            subprocess.PIPE,
            True  # capture_output
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Transformer failed: {result.stderr.decode()}")
        
        # Store additional Phase 2 output files
        job.tuples_output = f"tuples_{job.job_id}.json"
            
        return output_file
    
    async def _run_neo4j_backup(self, job: Job) -> str:
        """Run the Neo4j backup phase before upload."""
        
        backup_result_file = f"backup_result_{job.job_id}.json"
        
        cmd = [
            sys.executable,
            str(self.neo4j_manager_dir / "main.py"),
            "--action", "backup",
            "--job-id", job.job_id
        ]
        
        logger.info(f"Running Neo4j backup: {' '.join(cmd)}")
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            subprocess.run,
            cmd,
            subprocess.PIPE,
            subprocess.PIPE,
            True  # capture_output
        )
        
        if result.returncode != 0:
            logger.warning(f"Backup failed: {result.stderr.decode()}")
            # Continue with upload even if backup fails
            # In production, you might want to make this configurable
        
        return backup_result_file

    async def _run_uploader(self, job: Job) -> str:
        """Run the uploader phase with integrated backup management."""
        
        # Ensure we have cypher commands from Phase 2
        if not job.cypher_commands or not Path(job.cypher_commands).exists():
            raise RuntimeError("Phase 2 output not found - cannot proceed with upload")
        
        upload_result_file = f"upload_result_{job.job_id}.json"
        
        cmd = [
            sys.executable,
            str(self.uploader_dir / "main.py"),
            "--input", job.cypher_commands,
            "--job-id", job.job_id,
            "--output", upload_result_file,
            "--clear-database", "true"  # Always clear before upload
        ]
        
        logger.info(f"Running uploader: {' '.join(cmd)}")
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            subprocess.run,
            cmd,
            subprocess.PIPE,
            subprocess.PIPE,
            True  # capture_output
        )
        
        if result.returncode != 0:
            # If upload fails, offer to restore backup
            logger.error(f"Upload failed: {result.stderr.decode()}")
            
            if job.backup_result:
                logger.info("Upload failed - backup available for restoration")
                # Could trigger automatic restore here or leave for manual operation
            
            raise RuntimeError(f"Uploader failed: {result.stderr.decode()}")
        
        return upload_result_file


# Create FastAPI app
app = FastAPI(
    title="AST Parser Orchestrator",
    description="Orchestrates the multi-phase AST parsing pipeline",
    version="1.0.0"
)

# Create orchestration service
orchestrator = OrchestrationService()


@app.post("/v1/analyze", response_model=Dict[str, str])
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Start a new code analysis job.
    
    This endpoint initiates the three-phase pipeline:
    1. Extraction - Parse code and extract structure
    2. Transformation - Convert to Neo4j Cypher commands
    3. Loading - Load data into Neo4j database
    """
    # Validate codebase path
    codebase_path = Path(request.codebase_path)
    if not codebase_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Codebase path does not exist: {request.codebase_path}"
        )
    if not codebase_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Codebase path is not a directory: {request.codebase_path}"
        )
        
    # Create job
    job_id = orchestrator.create_job(str(codebase_path))
    
    # Start pipeline in background
    background_tasks.add_task(orchestrator.run_pipeline, job_id)
    
    return {
        "job_id": job_id,
        "status": "Analysis started",
        "message": f"Processing codebase at: {codebase_path}"
    }


@app.get("/v1/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the current status of an analysis job.
    
    This endpoint provides real-time updates on job progress,
    including the current phase and any error information.
    """
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )
        
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        phase=job.phase,
        progress=job.progress,
        message=job.message,
        started_at=job.started_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
        metadata=job.metadata
    )


@app.get("/v1/jobs/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: str) -> JobResultsResponse:
    """
    Get the results of a completed analysis job.
    
    This endpoint provides access to the output files generated
    by each phase of the pipeline.
    """
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )
        
    if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Job is still running. Current status: {job.status}"
        )
        
    return JobResultsResponse(
        job_id=job.job_id,
        status=job.status,
        extraction_output=job.extraction_output,
        cypher_commands=job.cypher_commands,
        tuples_output=job.tuples_output,
        loader_output=job.loader_output,
        # Phase 3 outputs
        backup_result=job.backup_result,
        upload_result=job.upload_result,
        neo4j_stats=job.neo4j_stats,
        metrics=job.metrics
    )


@app.get("/v1/jobs/{job_id}/files/{file_type}")
async def download_job_file(job_id: str, file_type: str) -> FileResponse:
    """
    Download a specific output file from a job.
    
    File types:
    - extraction: The extraction_output.json file
    - cypher: The cypher_commands.cypher file
    - tuples: The tuples.json file (Phase 2 JSON output)
    - loader: The loader output file
    - backup-result: The backup result file (Phase 3)
    - upload-result: The upload result file (Phase 3)
    """
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )
        
    file_map = {
        "extraction": job.extraction_output,
        "cypher": job.cypher_commands,
        "tuples": job.tuples_output,
        "loader": job.loader_output,
        "backup-result": job.backup_result,
        "upload-result": job.upload_result
    }
    
    file_path = file_map.get(file_type)
    if not file_path:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_type}. Available: {list(file_map.keys())}"
        )
        
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found for job {job_id}: {file_type}"
        )
        
    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="application/octet-stream"
    )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8078)