"""
Backup Management API Router

Provides REST endpoints for managing Neo4j database backups.
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import Phase 3 components
from neo4j_manager import BackupService, DatabaseTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/backups", tags=["backups"])

# Initialize services
backup_service = BackupService()
database_tracker = DatabaseTracker()


class BackupRequest(BaseModel):
    """Request model for creating a backup."""
    job_id: str
    description: str = None


class RestoreRequest(BaseModel):
    """Request model for restoring a backup."""
    job_id: str


@router.get("/")
async def list_all_backups() -> Dict[str, Any]:
    """List all available database backups."""
    
    try:
        backups = await database_tracker.list_all_backups(include_missing=False)
        
        return {
            "backups": [
                {
                    "job_id": backup.job_id,
                    "created_at": backup.created_at.isoformat(),
                    "backup_path": backup.backup_path,
                    "size_mb": backup.size_mb,
                    "description": backup.description or f"Backup for job {backup.job_id}",
                    "exists": backup.exists()
                }
                for backup in backups
            ],
            "total_backups": len(backups)
        }
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Create a new database backup."""
    
    try:
        # Start backup in background
        async def backup_task():
            result = await backup_service.create_backup(
                job_id=request.job_id,
                description=request.description
            )
            
            if result.success:
                logger.info(f"Backup created successfully for job {request.job_id}")
            else:
                logger.error(f"Backup failed for job {request.job_id}: {result.errors}")
        
        background_tasks.add_task(backup_task)
        
        return {
            "job_id": request.job_id,
            "message": "Backup creation initiated",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@router.get("/{job_id}")
async def get_backup_status(job_id: str) -> Dict[str, Any]:
    """Get backup status for a specific job."""
    
    try:
        backup = await database_tracker.get_backup_by_job_id(job_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"No backup found for job ID: {job_id}"
            )
        
        return {
            "job_id": job_id,
            "backup_completed": True,
            "backup_info": backup.to_dict(),
            "can_restore": backup.exists()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup status: {str(e)}")


@router.post("/{job_id}/restore")
async def restore_backup(
    job_id: str, 
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Restore Neo4j database from a specific backup."""
    
    try:
        # Check if backup exists
        backup = await database_tracker.get_backup_by_job_id(job_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"No backup found for job ID: {job_id}"
            )
        
        if not backup.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file no longer exists: {backup.backup_path}"
            )
        
        # Trigger restore in background
        async def restore_task():
            result = await backup_service.restore_backup(job_id)
            
            if result.success:
                logger.info(f"Backup restored successfully for job {job_id}")
            else:
                logger.error(f"Backup restore failed for job {job_id}: {result.errors}")
        
        background_tasks.add_task(restore_task)
        
        return {
            "job_id": job_id,
            "message": "Backup restore initiated",
            "backup_path": backup.backup_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")


@router.delete("/{job_id}")
async def delete_backup(job_id: str) -> Dict[str, str]:
    """Delete a specific backup."""
    
    try:
        success = await database_tracker.delete_backup(job_id)
        
        if success:
            return {
                "job_id": job_id,
                "message": "Backup deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Backup not found or could not be deleted: {job_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@router.get("/{job_id}/download")
async def download_backup_file(job_id: str) -> FileResponse:
    """Download the actual backup tarball file for a job."""
    
    try:
        backup = await database_tracker.get_backup_by_job_id(job_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"No backup found for job ID: {job_id}"
            )
        
        backup_path = Path(backup.backup_path)
        if not backup_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file not found: {backup.backup_path}"
            )
        
        return FileResponse(
            path=str(backup_path),
            filename=f"neo4j_backup_{job_id}.tar.gz",
            media_type="application/gzip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download backup: {str(e)}")


@router.get("/statistics/storage")
async def get_storage_statistics() -> Dict[str, Any]:
    """Get backup storage statistics."""
    
    try:
        stats = await database_tracker.get_storage_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get storage statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage statistics: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_backups(
    max_age_days: int = 30,
    keep_minimum: int = 5
) -> Dict[str, Any]:
    """Clean up old backups based on age and count limits."""
    
    try:
        result = await backup_service.cleanup_old_backups(max_age_days, keep_minimum)
        return result
        
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {str(e)}")


@router.post("/database/clear")
async def clear_database(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Clear the Neo4j database (with automatic backup)."""
    
    try:
        # Clear database in background
        async def clear_task():
            result = await backup_service.clear_database()
            
            if result.success:
                logger.info("Database cleared successfully")
            else:
                logger.error(f"Database clear failed: {result.errors}")
        
        background_tasks.add_task(clear_task)
        
        return {
            "message": "Database clear initiated (backup created first)",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")