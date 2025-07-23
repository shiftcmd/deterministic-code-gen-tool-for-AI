"""
Analysis routes for the Python Debug Tool API.
Clean API layer - delegates to service layer for business logic.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import service layer (after path modification)
try:
    from services.file_service import FileSystemService
except ImportError:
    # Fallback for development
    FileSystemService = None

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize services
file_service = FileSystemService()

# Simple in-memory cache for demo purposes
# In production, this would be in a proper database or Redis
analysis_cache: Dict[str, Dict[str, Any]] = {}


class AnalysisRequest(BaseModel):
    """Analysis request model."""
    path: str
    config_preset: str = "standard"
    include_relationships: bool = True
    export_to_neo4j: bool = False
    cache_results: bool = True


class CopyForAnalysisRequest(BaseModel):
    """Copy files for analysis request model."""
    source_path: str
    python_only: bool = True
    file_patterns: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    """Analysis response model."""
    run_id: str
    status: str
    message: str
    progress: int = 0


@router.post("/analysis/copy-for-analysis")
async def copy_files_for_analysis(request: CopyForAnalysisRequest) -> Dict[str, Any]:
    """
    Copy project files to analysis directory for safe parsing.
    
    This implements the proper architecture:
    1. Copy files to isolated analysis directory
    2. Perform analysis on copies, not originals
    3. Return session info for further analysis
    """
    try:
        # Delegate to service layer
        result = await file_service.copy_files_for_analysis(
            source_path=request.source_path,
            file_patterns=request.file_patterns,
            python_only=request.python_only
        )
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error copying files for analysis: {str(e)}"
        )


@router.post("/projects/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Start analysis of a Python project.
    
    This is a simplified version that creates a mock analysis job.
    In a full implementation, this would delegate to an analysis service.
    """
    
    try:
        # Generate a unique run ID
        run_id = f"run_{int(time.time())}"
        
        # Create analysis job entry
        analysis_cache[run_id] = {
            "run_id": run_id,
            "status": "queued",
            "progress": 0,
            "message": "Analysis queued for processing",
            "started_at": time.time(),
            "request": request.dict(),
            "python_files_count": 0  # Will be updated during processing
        }
        
        # TODO: In real implementation, this would:
        # 1. Validate the project path using file service
        # 2. Queue the analysis job in a task queue
        # 3. Start background processing
        # 4. Return immediately with job ID
        
        return AnalysisResponse(
            run_id=run_id,
            status="queued",
            message="Analysis job created successfully",
            progress=0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/processing/status/{run_id}")
async def get_processing_status(run_id: str) -> Dict[str, Any]:
    """Get the status of a processing job."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Analysis run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    return {
        "run_id": run_id,
        "status": analysis["status"],
        "progress": analysis["progress"],
        "message": analysis["message"],
        "started_at": analysis["started_at"],
        "python_files_count": analysis.get("python_files_count", 0)
    }


@router.post("/processing/stop/{run_id}")
async def stop_processing(run_id: str) -> Dict[str, Any]:
    """Stop a processing job."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Analysis run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    # Update status to cancelled
    analysis["status"] = "cancelled"
    analysis["message"] = "Analysis cancelled by user"
    analysis["completed_at"] = time.time()
    
    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Analysis stopped successfully"
    } 