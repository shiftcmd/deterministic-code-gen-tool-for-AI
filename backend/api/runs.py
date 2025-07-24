"""
Analysis runs management routes for the Python Debug Tool API.

This module provides endpoints for managing and retrieving analysis run results.
"""

import time
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Import the analysis cache from analysis module
from .analysis import analysis_cache
# Import orchestrator client for detailed results
from .orchestrator_client import orchestrator_client

router = APIRouter(prefix="/api", tags=["runs"])


class RunFilter(BaseModel):
    """Filter criteria for runs."""
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.get("/runs")
async def get_runs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of runs to return"),
    offset: int = Query(0, description="Number of runs to skip")
) -> Dict[str, Any]:
    """Get all analysis runs with optional filtering."""
    
    all_runs = []
    
    for run_id, analysis in analysis_cache.items():
        run_info = {
            "run_id": run_id,
            "status": analysis["status"],
            "progress": analysis["progress"],
            "message": analysis["message"],
            "started_at": analysis["started_at"],
            "config_preset": analysis.get("request", {}).get("config_preset", "unknown"),
            "base_path": analysis.get("request", {}).get("path", "unknown")
        }
        
        # Add completion info if available
        if "completed_at" in analysis:
            run_info["completed_at"] = analysis["completed_at"]
            run_info["duration"] = analysis["completed_at"] - analysis["started_at"]
        
        # Add results summary if available
        if "results" in analysis:
            results = analysis["results"]
            run_info["summary"] = {
                "modules": results.get("modules", 0),
                "classes": results.get("classes", 0),
                "functions": results.get("functions", 0),
                "relationships": results.get("relationships", 0)
            }
        
        # Add error info if failed
        if "error" in analysis:
            run_info["error"] = analysis["error"]
        
        all_runs.append(run_info)
    
    # Filter by status if requested
    if status:
        all_runs = [run for run in all_runs if run["status"] == status]
    
    # Sort by started_at (newest first)
    all_runs.sort(key=lambda x: x["started_at"], reverse=True)
    
    # Apply pagination
    total_count = len(all_runs)
    paginated_runs = all_runs[offset:offset + limit]
    
    return {
        "runs": paginated_runs,
        "total_count": total_count,
        "showing": len(paginated_runs),
        "offset": offset,
        "limit": limit,
        "has_more": total_count > offset + limit,
        "status": "success"
    }


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific analysis run."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    # Build comprehensive run details
    run_details = {
        "run_id": run_id,
        "status": analysis["status"],
        "progress": analysis["progress"],
        "message": analysis["message"],
        "started_at": analysis["started_at"],
        "request": analysis.get("request", {}),
        "python_files_count": analysis.get("python_files_count", 0)
    }
    
    # Add timing information
    if "completed_at" in analysis:
        run_details["completed_at"] = analysis["completed_at"]
        run_details["duration"] = analysis["completed_at"] - analysis["started_at"]
        run_details["duration_human"] = f"{run_details['duration']:.2f} seconds"
    
    # Add detailed results if available
    if "results" in analysis:
        run_details["results"] = analysis["results"]
    
    # Add error details if failed
    if "error" in analysis:
        run_details["error"] = analysis["error"]
    
    return run_details


@router.get("/runs/{run_id}/dashboard")
async def get_run_dashboard(run_id: str) -> Dict[str, Any]:
    """Get dashboard-formatted data for a specific run."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    # Check if run is completed
    if analysis["status"] != "completed":
        return {
            "dashboard": {
                "status": analysis["status"],
                "progress": analysis["progress"],
                "message": analysis["message"],
                "charts": [],
                "metrics": {},
                "summary": f"Analysis {analysis['status']}"
            },
            "status": "pending"
        }
    
    # Get results from orchestrator if this is an orchestrator job
    results = analysis.get("results", {})
    if analysis.get("orchestrator_job"):
        try:
            orchestrator_results = await orchestrator_client.get_job_results(run_id)
            if orchestrator_results:
                results = orchestrator_results.get("results", {})
        except Exception as e:
            # Fallback to cached results if orchestrator unavailable
            pass
    
    # Create metrics summary
    metrics = {
        "total_modules": results.get("modules", 0),
        "total_classes": results.get("classes", 0),
        "total_functions": results.get("functions", 0),
        "total_variables": results.get("variables", 0),
        "total_imports": results.get("imports", 0),
        "total_relationships": results.get("relationships", 0),
        "analysis_time": results.get("analysis_time", 0),
        "python_files_analyzed": analysis.get("python_files_count", 0)
    }
    
    # Create chart data
    charts = [
        {
            "type": "pie",
            "title": "Code Elements Distribution",
            "data": [
                {"name": "Classes", "value": metrics["total_classes"]},
                {"name": "Functions", "value": metrics["total_functions"]},
                {"name": "Variables", "value": metrics["total_variables"]},
                {"name": "Imports", "value": metrics["total_imports"]}
            ]
        },
        {
            "type": "bar",
            "title": "Analysis Metrics",
            "data": [
                {"category": "Modules", "value": metrics["total_modules"]},
                {"category": "Relationships", "value": metrics["total_relationships"]},
                {"category": "Files", "value": metrics["python_files_analyzed"]}
            ]
        }
    ]
    
    # Create summary text
    duration = analysis.get("completed_at", 0) - analysis["started_at"]
    summary = f"Analyzed {metrics['python_files_analyzed']} Python files in {duration:.2f}s"
    
    return {
        "dashboard": {
            "metrics": metrics,
            "charts": charts,
            "summary": summary,
            "completion_time": analysis.get("completed_at"),
            "base_path": results.get("base_path", "unknown"),
            "neo4j_exported": results.get("neo4j_exported", False)
        },
        "status": "success"
    }


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str) -> Dict[str, Any]:
    """Delete an analysis run and its results."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    # Check if run is still in progress
    analysis = analysis_cache[run_id]
    if analysis["status"] in ["queued", "running"]:
        raise HTTPException(
            status_code=409, 
            detail="Cannot delete a run that is currently in progress"
        )
    
    # Delete the run
    del analysis_cache[run_id]
    
    return {
        "message": f"Run {run_id} deleted successfully",
        "deleted_run_id": run_id,
        "status": "success"
    }


@router.get("/runs/{run_id}/files")
async def get_run_files(run_id: str) -> Dict[str, Any]:
    """Get the list of files that were analyzed in a specific run."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    # Get base path from request
    base_path = analysis.get("request", {}).get("path", ".")
    
    return {
        "run_id": run_id,
        "base_path": base_path,
        "python_files_count": analysis.get("python_files_count", 0),
        "status": analysis["status"],
        "files": [],  # TODO: Could be populated from parser results
        "message": "File listing not yet implemented in parser results"
    }


@router.get("/runs/{run_id}/metrics")
async def get_run_metrics(run_id: str) -> Dict[str, Any]:
    """Get detailed metrics for a specific analysis run."""
    
    if run_id not in analysis_cache:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    
    analysis = analysis_cache[run_id]
    
    if analysis["status"] != "completed":
        return {
            "message": "Metrics not available - analysis not completed",
            "status": analysis["status"],
            "progress": analysis["progress"]
        }
    
    results = analysis.get("results", {})
    timing = {
        "started_at": analysis["started_at"],
        "completed_at": analysis.get("completed_at"),
        "duration": analysis.get("completed_at", 0) - analysis["started_at"],
        "analysis_time": results.get("analysis_time", 0)
    }
    
    return {
        "run_id": run_id,
        "metrics": results,
        "timing": timing,
        "configuration": analysis.get("request", {}),
        "status": "success"
    } 