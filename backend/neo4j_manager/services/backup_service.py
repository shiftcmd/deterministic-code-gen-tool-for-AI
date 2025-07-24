"""
Backup Service - High-level backup workflow orchestration

Provides automated backup workflows that integrate backup creation,
registration, and version tracking.
"""

import logging
from typing import Optional, Dict, Any

from ..core.backup_manager import BackupManager
from ..core.database_tracker import DatabaseTracker
from ..models.backup_metadata import BackupResult, RestoreResult

logger = logging.getLogger(__name__)


class BackupService:
    """High-level backup service orchestrator."""
    
    def __init__(
        self,
        backup_manager: Optional[BackupManager] = None,
        database_tracker: Optional[DatabaseTracker] = None
    ):
        self.backup_manager = backup_manager or BackupManager()
        self.database_tracker = database_tracker or DatabaseTracker()
    
    async def create_backup(
        self, 
        job_id: str,
        description: Optional[str] = None,
        **metadata
    ) -> BackupResult:
        """
        Create a backup with automatic registration and version tracking.
        
        Args:
            job_id: Job identifier for this backup
            description: Optional description for the backup
            **metadata: Additional metadata (neo4j_version, node_count, etc.)
        
        Returns:
            BackupResult with operation status
        """
        try:
            logger.info(f"Starting backup workflow for job {job_id}")
            
            # Create the backup
            backup_result = await self.backup_manager.create_backup(job_id)
            
            if backup_result.success and backup_result.backup_path:
                # Register the backup
                await self.database_tracker.register_backup(
                    job_id=job_id,
                    backup_path=backup_result.backup_path,
                    description=description or f"Backup for job {job_id}",
                    **metadata
                )
                
                # Add database version
                await self.database_tracker.add_database_version(
                    job_id=job_id,
                    backup_path=backup_result.backup_path,
                    description=description,
                    **metadata
                )
                
                logger.info(f"Backup workflow completed successfully for job {job_id}")
            else:
                logger.error(f"Backup workflow failed for job {job_id}: {backup_result.errors}")
            
            return backup_result
            
        except Exception as e:
            logger.error(f"Backup workflow failed for job {job_id}: {e}")
            # Return a failed result
            result = BackupResult(job_id=job_id)
            result.add_error(str(e))
            return result
    
    async def restore_backup(self, job_id: str) -> RestoreResult:
        """
        Restore a backup with automatic version tracking.
        
        Args:
            job_id: Job identifier for the backup to restore
        
        Returns:
            RestoreResult with operation status
        """
        try:
            logger.info(f"Starting restore workflow for job {job_id}")
            
            # Get backup metadata
            backup_metadata = await self.database_tracker.get_backup_by_job_id(job_id)
            if not backup_metadata:
                result = RestoreResult(job_id=job_id)
                result.add_error(f"No backup found for job ID: {job_id}")
                return result
            
            if not backup_metadata.exists():
                result = RestoreResult(job_id=job_id)
                result.add_error(f"Backup file no longer exists: {backup_metadata.backup_path}")
                return result
            
            # Perform the restore
            restore_result = await self.backup_manager.restore_backup(job_id, backup_metadata.backup_path)
            
            if restore_result.success:
                # Update version tracking to mark this version as active
                version = await self.database_tracker.get_database_version_by_job_id(job_id)
                if version:
                    # Add the restored version as a new active version
                    await self.database_tracker.add_database_version(
                        job_id=f"{job_id}_restored",
                        backup_path=backup_metadata.backup_path,
                        description=f"Restored from backup {job_id}",
                        source_codebase=version.source_codebase,
                        extraction_job_id=version.extraction_job_id,
                        transformation_job_id=version.transformation_job_id,
                        node_count=version.node_count,
                        relationship_count=version.relationship_count,
                        property_count=version.property_count,
                        tags=version.tags + ["restored"]
                    )
                
                logger.info(f"Restore workflow completed successfully for job {job_id}")
            else:
                logger.error(f"Restore workflow failed for job {job_id}: {restore_result.errors}")
            
            return restore_result
            
        except Exception as e:
            logger.error(f"Restore workflow failed for job {job_id}: {e}")
            # Return a failed result
            result = RestoreResult(job_id=job_id)
            result.add_error(str(e))
            return result
    
    async def clear_database(self) -> BackupResult:
        """
        Clear the database with automatic backup before clearing.
        
        Returns:
            BackupResult with operation status
        """
        try:
            logger.info("Starting database clear workflow")
            
            # Create a backup before clearing (safety measure)
            clear_job_id = f"pre_clear_backup_{int(datetime.now().timestamp())}"
            backup_result = await self.create_backup(
                job_id=clear_job_id,
                description="Automatic backup before database clear"
            )
            
            if not backup_result.success:
                logger.warning("Pre-clear backup failed, proceeding with clear anyway")
            
            # Clear the database
            clear_result = await self.backup_manager.clear_database()
            
            if clear_result.success:
                logger.info("Database clear workflow completed successfully")
            else:
                logger.error(f"Database clear workflow failed: {clear_result.errors}")
            
            return clear_result
            
        except Exception as e:
            logger.error(f"Database clear workflow failed: {e}")
            # Return a failed result
            result = BackupResult(job_id="clear_operation")
            result.add_error(str(e))
            return result
    
    async def list_backups(self, include_missing: bool = False) -> Dict[str, Any]:
        """
        List all backups with metadata.
        
        Args:
            include_missing: Whether to include backups whose files no longer exist
        
        Returns:
            Dictionary with backup information
        """
        try:
            backups = await self.database_tracker.list_all_backups(include_missing)
            versions = await self.database_tracker.list_database_versions()
            stats = await self.database_tracker.get_storage_statistics()
            
            return {
                "backups": [backup.to_dict() for backup in backups],
                "versions": [version.to_dict() for version in versions],
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return {
                "backups": [],
                "versions": [],
                "statistics": {},
                "error": str(e)
            }
    
    async def cleanup_old_backups(self, max_age_days: int = 30, keep_minimum: int = 5) -> Dict[str, Any]:
        """
        Clean up old backups based on age and count limits.
        
        Args:
            max_age_days: Maximum age in days for backups to keep
            keep_minimum: Minimum number of backups to always keep
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            logger.info(f"Starting backup cleanup: max_age_days={max_age_days}, keep_minimum={keep_minimum}")
            
            all_backups = await self.database_tracker.list_all_backups(include_missing=False)
            
            # Sort by creation date (newest first)
            sorted_backups = sorted(all_backups, key=lambda b: b.created_at, reverse=True)
            
            # Determine which backups to delete
            to_delete = []
            to_keep = []
            
            for i, backup in enumerate(sorted_backups):
                # Always keep the minimum number of most recent backups
                if i < keep_minimum:
                    to_keep.append(backup)
                    continue
                
                # Delete backups older than max_age_days
                if backup.age_days > max_age_days:
                    to_delete.append(backup)
                else:
                    to_keep.append(backup)
            
            # Delete the identified backups
            deleted_count = 0
            deleted_size_mb = 0.0
            failed_deletions = []
            
            for backup in to_delete:
                success = await self.database_tracker.delete_backup(backup.job_id)
                if success:
                    deleted_count += 1
                    deleted_size_mb += backup.size_mb
                else:
                    failed_deletions.append(backup.job_id)
            
            # Also cleanup missing entries
            missing_cleaned = await self.database_tracker.cleanup_missing_backups()
            
            result = {
                "deleted_count": deleted_count,
                "deleted_size_mb": deleted_size_mb,
                "kept_count": len(to_keep),
                "failed_deletions": failed_deletions,
                "missing_cleaned": len(missing_cleaned),
                "missing_job_ids": missing_cleaned
            }
            
            logger.info(f"Backup cleanup completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {
                "deleted_count": 0,
                "deleted_size_mb": 0.0,
                "kept_count": 0,
                "failed_deletions": [],
                "missing_cleaned": 0,
                "missing_job_ids": [],
                "error": str(e)
            }


from datetime import datetime  # Import needed for clear_database method