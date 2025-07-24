"""
FastAPI endpoints for transformation operations.

Provides REST API and WebSocket endpoints for the Transformation domain
with real-time progress updates for the UI.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field

from transformer.main import TransformationOrchestrator, transform_file
from transformer.models.metadata import TransformationStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transform", tags=["transformation"])

# Active transformations registry
active_transformations: Dict[str, TransformationOrchestrator] = {}
# WebSocket connections for real-time updates
websocket_connections: Dict[str, List[WebSocket]] = {}


class TransformationRequest(BaseModel):
    """Request model for starting a transformation."""
    extraction_file: str = Field(..., description="Path to extraction JSON file")
    output_directory: Optional[str] = Field(".", description="Output directory for results")
    output_formats: List[str] = Field(["neo4j"], description="List of output formats")
    job_id: Optional[str] = Field(None, description="Optional custom job ID")


class TransformationJob(BaseModel):
    """Response model for transformation job."""
    job_id: str
    status: str
    message: str
    started_at: datetime
    metadata: Dict[str, Any]


class TransformationProgress(BaseModel):
    """Response model for transformation progress."""
    job_id: str
    status: str
    progress_percentage: float
    current_step: str
    metadata: Dict[str, Any]


class TransformationResult(BaseModel):
    """Response model for transformation results."""
    job_id: str
    success: bool
    output_files: Dict[str, str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class ValidationResult(BaseModel):
    """Response model for transformation validation."""
    job_id: str
    validation_passed: bool
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]


@router.post("/start", response_model=TransformationJob)
async def start_transformation(
    request: TransformationRequest,
    background_tasks: BackgroundTasks
) -> TransformationJob:
    """
    Start a new transformation job.
    
    Args:
        request: Transformation request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        TransformationJob with job details
    """
    try:
        # Validate input file exists
        input_file = Path(request.extraction_file)
        if not input_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Extraction file not found: {request.extraction_file}"
            )
        
        # Create orchestrator
        orchestrator = TransformationOrchestrator(
            job_id=request.job_id,
            enable_progress_reporting=True
        )
        
        # Store in active transformations
        active_transformations[orchestrator.job_id] = orchestrator
        
        # Start transformation in background
        background_tasks.add_task(
            _run_transformation,
            orchestrator,
            request.extraction_file,
            request.output_directory,
            request.output_formats
        )
        
        logger.info(f"Started transformation job: {orchestrator.job_id}")
        
        return TransformationJob(
            job_id=orchestrator.job_id,
            status=TransformationStatus.RUNNING.value,
            message="Transformation started",
            started_at=datetime.utcnow(),
            metadata=orchestrator.get_job_status()
        )
        
    except Exception as e:
        logger.error(f"Failed to start transformation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/progress", response_model=TransformationProgress)
async def get_transformation_progress(job_id: str) -> TransformationProgress:
    """
    Get current progress of a transformation job.
    
    Args:
        job_id: Transformation job ID
        
    Returns:
        TransformationProgress with current status
    """
    orchestrator = active_transformations.get(job_id)
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Transformation job not found: {job_id}"
        )
    
    metadata = orchestrator.get_job_status()
    
    return TransformationProgress(
        job_id=job_id,
        status=metadata["status"],
        progress_percentage=metadata["progress_percentage"],
        current_step=metadata["current_step"],
        metadata=metadata
    )


@router.get("/{job_id}/results", response_model=TransformationResult)
async def get_transformation_results(job_id: str) -> TransformationResult:
    """
    Get results of a completed transformation job.
    
    Args:
        job_id: Transformation job ID
        
    Returns:
        TransformationResult with output files and statistics
    """
    orchestrator = active_transformations.get(job_id)
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Transformation job not found: {job_id}"
        )
    
    metadata = orchestrator.get_job_status()
    
    # Check if transformation is complete
    if metadata["status"] not in [TransformationStatus.COMPLETED.value, TransformationStatus.FAILED.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Transformation is still {metadata['status']}"
        )
    
    # TODO: Extract actual results from orchestrator
    # For now, return basic structure
    return TransformationResult(
        job_id=job_id,
        success=metadata["status"] == TransformationStatus.COMPLETED.value,
        output_files={},  # TODO: Get from orchestrator result
        errors=[],  # TODO: Get from orchestrator result
        warnings=[],  # TODO: Get from orchestrator result
        metadata=metadata
    )


@router.post("/{job_id}/validate", response_model=ValidationResult)
async def validate_transformation(job_id: str) -> ValidationResult:
    """
    Validate transformation results.
    
    Args:
        job_id: Transformation job ID
        
    Returns:
        ValidationResult with validation status
    """
    orchestrator = active_transformations.get(job_id)
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Transformation job not found: {job_id}"
        )
    
    # TODO: Implement actual validation logic
    # For now, return basic validation
    return ValidationResult(
        job_id=job_id,
        validation_passed=True,
        errors=[],
        warnings=[],
        statistics={}
    )


@router.delete("/{job_id}")
async def cancel_transformation(job_id: str) -> Dict[str, str]:
    """
    Cancel a running transformation job.
    
    Args:
        job_id: Transformation job ID
        
    Returns:
        Cancellation status
    """
    orchestrator = active_transformations.get(job_id)
    if not orchestrator:
        raise HTTPException(
            status_code=404,
            detail=f"Transformation job not found: {job_id}"
        )
    
    # TODO: Implement actual cancellation logic
    # For now, just remove from active transformations
    del active_transformations[job_id]
    
    logger.info(f"Cancelled transformation job: {job_id}")
    
    return {"message": f"Transformation {job_id} cancelled"}


@router.websocket("/ws/{job_id}")
async def transformation_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time transformation progress updates.
    
    Args:
        websocket: WebSocket connection
        job_id: Transformation job ID
    """
    await websocket.accept()
    
    # Add to connections registry
    if job_id not in websocket_connections:
        websocket_connections[job_id] = []
    websocket_connections[job_id].append(websocket)
    
    try:
        # Check if job exists
        orchestrator = active_transformations.get(job_id)
        if not orchestrator:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Transformation job not found: {job_id}"
            }))
            return
        
        # Send initial status
        metadata = orchestrator.get_job_status()
        await websocket.send_text(json.dumps({
            "type": "status",
            "data": metadata
        }))
        
        # Keep connection alive and send updates
        while True:
            # Send periodic updates
            current_metadata = orchestrator.get_job_status()
            await websocket.send_text(json.dumps({
                "type": "progress",
                "data": current_metadata
            }))
            
            # Check if job is complete
            if current_metadata["status"] in [TransformationStatus.COMPLETED.value, TransformationStatus.FAILED.value]:
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "data": current_metadata
                }))
                break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        # Remove from connections
        if job_id in websocket_connections:
            websocket_connections[job_id].remove(websocket)
            if not websocket_connections[job_id]:
                del websocket_connections[job_id]


async def _run_transformation(
    orchestrator: TransformationOrchestrator,
    extraction_file: str,
    output_directory: str,
    output_formats: List[str]
) -> None:
    """
    Background task to run transformation.
    
    Args:
        orchestrator: TransformationOrchestrator instance
        extraction_file: Path to extraction file
        output_directory: Output directory
        output_formats: List of output formats
    """
    try:
        # Load extraction data
        with open(extraction_file, 'r', encoding='utf-8') as f:
            extraction_data = json.load(f)
        
        # Run transformation
        result = await orchestrator.transform_extraction_data(
            extraction_data,
            output_formats,
            output_directory
        )
        
        # Notify WebSocket connections
        await _notify_websocket_connections(orchestrator.job_id, {
            "type": "complete",
            "data": orchestrator.get_job_status()
        })
        
        logger.info(f"Transformation completed: {orchestrator.job_id}")
        
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        
        # Notify WebSocket connections of error
        await _notify_websocket_connections(orchestrator.job_id, {
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up after some time
        await asyncio.sleep(300)  # Keep results for 5 minutes
        if orchestrator.job_id in active_transformations:
            del active_transformations[orchestrator.job_id]


async def _notify_websocket_connections(job_id: str, message: Dict[str, Any]) -> None:
    """
    Notify all WebSocket connections for a job.
    
    Args:
        job_id: Job ID
        message: Message to send
    """
    if job_id not in websocket_connections:
        return
    
    # Send to all connections, removing failed ones
    connections = websocket_connections[job_id].copy()
    for websocket in connections:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
            websocket_connections[job_id].remove(websocket)
    
    # Clean up empty connection lists
    if not websocket_connections[job_id]:
        del websocket_connections[job_id]


# Utility endpoint for testing
@router.post("/test")
async def test_transformation(file_path: str) -> Dict[str, Any]:
    """
    Test endpoint for quick transformation testing.
    
    Args:
        file_path: Path to extraction file
        
    Returns:
        Test results
    """
    try:
        result = await transform_file(file_path)
        return {
            "success": result.success,
            "job_id": result.job_id,
            "metadata": result.metadata.to_dict(),
            "output_files": result.output_files,
            "errors": result.errors,
            "warnings": result.warnings
        }
    except Exception as e:
        logger.error(f"Test transformation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }