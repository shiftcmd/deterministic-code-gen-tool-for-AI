"""
Analysis routes for the Python Debug Tool API.
Clean API layer - delegates to orchestrator service for analysis processing.
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
    from parser.dev.services.file_service import FileSystemService
except ImportError:
    # Fallback for development
    FileSystemService = None

# Import orchestrator client
from .orchestrator_client import (
    orchestrator_client, 
    map_orchestrator_status_to_frontend,
    map_frontend_request_to_orchestrator
)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize services
file_service = FileSystemService()

# In-memory cache for analysis runs (for compatibility with existing frontend)
# In production, this would be in a proper database
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
    Start analysis of a Python project via orchestrator service.
    
    This delegates to the orchestrator service which runs the complete
    3-phase analysis pipeline (extraction, transformation, loading).
    """
    
    try:
        # First check if orchestrator is available
        orchestrator_available = await orchestrator_client.health_check()
        if not orchestrator_available:
            raise HTTPException(
                status_code=503, 
                detail="Analysis service unavailable. Please ensure the orchestrator is running on port 8000."
            )
        
        # Map frontend request to orchestrator format
        orchestrator_request = map_frontend_request_to_orchestrator(request.dict())
        
        # Start analysis via orchestrator
        orchestrator_response = await orchestrator_client.start_analysis(**orchestrator_request)
        
        job_id = orchestrator_response.get("job_id")
        if not job_id:
            raise Exception("No job ID returned from orchestrator")
        
        # Cache the job info for frontend compatibility
        analysis_cache[job_id] = {
            "run_id": job_id,
            "job_id": job_id,
            "status": "queued", 
            "progress": 0,
            "message": "Analysis started via orchestrator",
            "started_at": time.time(),
            "request": request.dict(),
            "orchestrator_job": True
        }
        
        return AnalysisResponse(
            run_id=job_id,
            status="queued",
            message="Analysis job started successfully",
            progress=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/processing/status/{run_id}")
async def get_processing_status(run_id: str) -> Dict[str, Any]:
    """Get the status of a processing job from orchestrator."""
    
    # Check if this is an orchestrator job
    if run_id in analysis_cache and analysis_cache[run_id].get("orchestrator_job"):
        try:
            # Get status from orchestrator
            orchestrator_status = await orchestrator_client.get_job_status(run_id)
            
            # Map to frontend format
            frontend_status = map_orchestrator_status_to_frontend(orchestrator_status)
            
            # Update cache
            analysis_cache[run_id].update(frontend_status)
            
            return frontend_status
            
        except Exception as e:
            # If orchestrator is unavailable, return cached status
            if run_id in analysis_cache:
                return analysis_cache[run_id]
            raise HTTPException(status_code=404, detail=f"Analysis run not found: {run_id}")
    
    # Fallback to cached analysis for legacy jobs
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
    """Stop a processing job via orchestrator."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Analysis run not found: {run_id}")
    
    # Check if this is an orchestrator job
    if analysis_cache[run_id].get("orchestrator_job"):
        try:
            # Stop job via orchestrator
            result = await orchestrator_client.stop_job(run_id)
            
            # Update cache
            analysis_cache[run_id]["status"] = "cancelled"
            analysis_cache[run_id]["message"] = "Analysis cancelled by user"
            analysis_cache[run_id]["completed_at"] = time.time()
            
            return {
                "run_id": run_id,
                "status": "cancelled", 
                "message": "Analysis stopped successfully"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop analysis: {str(e)}")
    
    # Fallback for legacy jobs
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


@router.get("/orchestrator/health")
async def check_orchestrator_health() -> Dict[str, Any]:
    """Check if orchestrator service is available."""
    
    try:
        is_available = await orchestrator_client.health_check()
        
        return {
            "orchestrator_available": is_available,
            "orchestrator_url": orchestrator_client.base_url,
            "status": "healthy" if is_available else "unavailable",
            "message": "Orchestrator service is reachable" if is_available else "Orchestrator service is not responding"
        }
        
    except Exception as e:
        return {
            "orchestrator_available": False,
            "orchestrator_url": orchestrator_client.base_url,
            "status": "error",
            "message": f"Error checking orchestrator: {str(e)}"
        } 