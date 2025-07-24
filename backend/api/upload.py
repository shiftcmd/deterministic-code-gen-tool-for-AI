"""
Upload Status API Router

Provides REST endpoints for monitoring Neo4j upload operations.
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/upload", tags=["upload"])


class ManualUploadRequest(BaseModel):
    """Request model for manual upload trigger."""
    cypher_file_path: str
    clear_database: bool = True
    validate_before_upload: bool = True


@router.get("/jobs/{job_id}/status")
async def get_upload_status(job_id: str) -> Dict[str, Any]:
    """Get detailed Neo4j upload status for a specific job."""
    
    try:
        # Import here to avoid circular imports
        from parser.prod.orchestrator.main import orchestrator
        
        job = orchestrator.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        # Load upload result if available
        upload_stats = None
        if job.upload_result and Path(job.upload_result).exists():
            with open(job.upload_result, 'r') as f:
                upload_stats = json.load(f)
        
        return {
            "job_id": job_id,
            "phase": job.phase,
            "status": job.status.value,
            "upload_completed": job.status.value == "completed",
            "upload_stats": upload_stats,
            "cypher_file_ready": bool(job.cypher_commands and Path(job.cypher_commands).exists()),
            "upload_result_available": bool(upload_stats),
            "backup_created": bool(job.backup_result)
        }
        
    except Exception as e:
        logger.error(f"Failed to get upload status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get upload status: {str(e)}")


@router.post("/jobs/{job_id}/trigger")
async def trigger_manual_upload(
    job_id: str,
    background_tasks: BackgroundTasks,
    upload_options: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Manually trigger Neo4j upload for completed Phase 2 job."""
    
    try:
        # Import here to avoid circular imports
        from parser.prod.orchestrator.main import orchestrator
        
        job = orchestrator.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        if not job.cypher_commands or not Path(job.cypher_commands).exists():
            raise HTTPException(
                status_code=400, 
                detail="Phase 2 must be completed before upload"
            )
        
        if job.upload_result:
            raise HTTPException(
                status_code=400,
                detail="Upload already completed for this job"
            )
        
        # Start Phase 3 upload in background
        async def upload_task():
            try:
                # Run backup first
                backup_result = await orchestrator._run_neo4j_backup(job)
                job.backup_result = backup_result
                
                # Then run upload
                upload_result = await orchestrator._run_uploader(job)
                job.upload_result = upload_result
                
                # Update job status
                orchestrator.update_job_status(
                    job_id,
                    job.status.__class__.COMPLETED,
                    "completed",
                    "Manual upload completed successfully"
                )
                
            except Exception as e:
                logger.error(f"Manual upload failed for job {job_id}: {e}")
                orchestrator.update_job_status(
                    job_id,
                    job.status.__class__.FAILED,
                    "upload_failed",
                    f"Manual upload failed: {str(e)}"
                )
        
        background_tasks.add_task(upload_task)
        
        return {
            "job_id": job_id,
            "message": "Upload started",
            "status": "Upload initiated in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger upload: {str(e)}")


@router.get("/jobs/{job_id}/neo4j-stats")
async def get_neo4j_stats(job_id: str) -> Dict[str, Any]:
    """Get detailed Neo4j upload statistics."""
    
    try:
        # Import here to avoid circular imports
        from parser.prod.orchestrator.main import orchestrator
        from config import get_settings
        
        job = orchestrator.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        if not job.upload_result or not Path(job.upload_result).exists():
            raise HTTPException(
                status_code=404,
                detail="Upload statistics not available"
            )
        
        with open(job.upload_result, 'r') as f:
            upload_stats = json.load(f)
        
        settings = get_settings()
        neo4j_config = settings.get_neo4j_config()
        
        return {
            "job_id": job_id,
            "upload_stats": upload_stats,
            "neo4j_connection": {
                "database": neo4j_config["database"],
                "uri": neo4j_config["uri"],
                "status": "connected"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Neo4j stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Neo4j stats: {str(e)}")


@router.post("/direct")
async def direct_upload(
    request: ManualUploadRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Direct upload from a Cypher file (bypasses orchestrator)."""
    
    try:
        from uploader import Neo4jClient, BatchUploader, ValidationService
        import uuid
        
        # Validate file exists
        cypher_file = Path(request.cypher_file_path)
        if not cypher_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Cypher file not found: {request.cypher_file_path}"
            )
        
        job_id = f"direct_upload_{str(uuid.uuid4())[:8]}"
        
        # Start upload in background
        async def direct_upload_task():
            try:
                # Initialize services
                neo4j_client = Neo4jClient()
                uploader = BatchUploader(neo4j_client)
                
                # Perform upload
                result = await uploader.upload_from_file(
                    request.cypher_file_path,
                    job_id=job_id,
                    validate_before_upload=request.validate_before_upload
                )
                
                # Save results
                result_file = f"direct_upload_result_{job_id}.json"
                with open(result_file, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)
                
                if result.success:
                    logger.info(f"Direct upload completed successfully: {job_id}")
                else:
                    logger.error(f"Direct upload failed: {job_id} - {result.errors}")
                    
            except Exception as e:
                logger.error(f"Direct upload task failed: {job_id} - {e}")
        
        background_tasks.add_task(direct_upload_task)
        
        return {
            "job_id": job_id,
            "message": "Direct upload initiated",
            "cypher_file": request.cypher_file_path,
            "status": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start direct upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start direct upload: {str(e)}")


@router.get("/health")
async def upload_service_health() -> Dict[str, Any]:
    """Check upload service health and Neo4j connectivity."""
    
    try:
        from uploader import Neo4jClient
        
        # Test Neo4j connection
        neo4j_client = Neo4jClient()
        health = await neo4j_client.health_check()
        
        return {
            "service": "upload",
            "status": "healthy" if health.healthy else "unhealthy",
            "neo4j_connection": health.to_dict(),
            "connection_stats": neo4j_client.get_connection_stats()
        }
        
    except Exception as e:
        logger.error(f"Upload service health check failed: {e}")
        return {
            "service": "upload", 
            "status": "unhealthy",
            "error": str(e)
        }