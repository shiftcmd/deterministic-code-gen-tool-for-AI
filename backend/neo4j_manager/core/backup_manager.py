"""
Backup Manager - Core Neo4j database backup and restore operations

Handles:
- Neo4j service lifecycle management (stop/start)
- Database file backup with tarball compression
- Backup restoration with validation
- Backup integrity verification
"""

import asyncio
import logging
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .neo4j_service import Neo4jService
from .tarball_manager import TarballManager
from ..models.backup_metadata import BackupResult, RestoreResult

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages Neo4j database backup and restore operations."""
    
    def __init__(
        self,
        neo4j_data_dir: Optional[str] = None,
        backup_storage_dir: Optional[str] = None,
        service_name: Optional[str] = None
    ):
        # Initialize from config if not provided
        if not neo4j_data_dir or not backup_storage_dir or not service_name:
            from config import get_settings
            settings = get_settings()
            
            self.neo4j_data_dir = Path(neo4j_data_dir or settings.database.neo4j_data_dir)
            self.backup_storage_dir = Path(backup_storage_dir or settings.database.neo4j_backup_dir)
            service_name = service_name or settings.database.neo4j_service_name
        else:
            self.neo4j_data_dir = Path(neo4j_data_dir)
            self.backup_storage_dir = Path(backup_storage_dir)
        
        # Ensure backup directory exists
        self.backup_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Services
        self.neo4j_service = Neo4jService(service_name)
        self.tarball_manager = TarballManager()
        
    async def create_backup(self, job_id: str) -> BackupResult:
        """Create a complete backup of the current Neo4j database."""
        
        result = BackupResult(job_id=job_id)
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting database backup for job {job_id}")
            
            # Stop Neo4j service to ensure data consistency
            logger.info("Stopping Neo4j service for backup")
            stop_result = await self.neo4j_service.stop()
            if not stop_result.success:
                result.add_error(f"Failed to stop Neo4j: {stop_result.error}")
                return result
            
            # Verify database directory exists
            if not self.neo4j_data_dir.exists():
                result.add_error(f"Neo4j data directory not found: {self.neo4j_data_dir}")
                return result
            
            # Create backup filename with job_id and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"neo4j_backup_{job_id}_{timestamp}.tar.gz"
            backup_path = self.backup_storage_dir / backup_filename
            
            # Create tarball backup
            logger.info(f"Creating tarball backup: {backup_path}")
            tarball_result = await self.tarball_manager.create_tarball(
                source_dir=self.neo4j_data_dir,
                target_path=backup_path,
                compression="gzip"
            )
            
            if not tarball_result.success:
                result.add_error(f"Tarball creation failed: {tarball_result.error}")
                return result
            
            # Restart Neo4j service
            logger.info("Restarting Neo4j service")
            start_result = await self.neo4j_service.start()
            if not start_result.success:
                result.add_error(f"Failed to restart Neo4j: {start_result.error}")
                # Continue - backup was successful even if restart failed
            
            # Calculate backup statistics
            backup_size = backup_path.stat().st_size
            backup_duration = (datetime.now() - start_time).total_seconds()
            
            # Update result
            result.backup_path = str(backup_path)
            result.backup_size_bytes = backup_size
            result.backup_duration_seconds = backup_duration
            result.success = True
            
            logger.info(f"Backup completed: {backup_path} ({backup_size / 1024 / 1024:.2f} MB)")
            
            return result
            
        except Exception as e:
            logger.error(f"Backup failed for job {job_id}: {e}")
            result.add_error(str(e))
            
            # Ensure Neo4j is restarted even if backup failed
            try:
                await self.neo4j_service.start()
            except Exception as restart_error:
                logger.error(f"Failed to restart Neo4j after backup failure: {restart_error}")
            
            return result
    
    async def restore_backup(self, job_id: str, backup_path: Optional[str] = None) -> RestoreResult:
        """Restore a Neo4j database from backup."""
        
        result = RestoreResult(job_id=job_id)
        start_time = datetime.now()
        
        try:
            # Find backup path if not provided
            if not backup_path:
                backup_path = await self._find_backup_for_job(job_id)
                if not backup_path:
                    result.add_error(f"No backup found for job ID: {job_id}")
                    return result
            
            backup_file = Path(backup_path)
            if not backup_file.exists():
                result.add_error(f"Backup file not found: {backup_path}")
                return result
            
            logger.info(f"Starting database restore from: {backup_path}")
            
            # Stop Neo4j service
            logger.info("Stopping Neo4j service for restore")
            stop_result = await self.neo4j_service.stop()
            if not stop_result.success:
                result.add_error(f"Failed to stop Neo4j: {stop_result.error}")
                return result
            
            # Clear current database
            logger.info("Clearing current database")
            if self.neo4j_data_dir.exists():
                shutil.rmtree(self.neo4j_data_dir)
            
            # Extract backup
            logger.info("Extracting backup")
            extract_result = await self.tarball_manager.extract_tarball(
                tarball_path=backup_file,
                target_dir=self.neo4j_data_dir.parent
            )
            
            if not extract_result.success:
                result.add_error(f"Backup extraction failed: {extract_result.error}")
                return result
            
            # Restart Neo4j service
            logger.info("Restarting Neo4j service")
            start_result = await self.neo4j_service.start()
            if not start_result.success:
                result.add_error(f"Failed to restart Neo4j: {start_result.error}")
                return result
            
            # Wait for Neo4j to be ready
            ready_result = await self.neo4j_service.wait_for_ready(timeout_seconds=60)
            if not ready_result.success:
                result.add_error(f"Neo4j failed to start properly: {ready_result.error}")
                return result
            
            result.backup_path = str(backup_path)
            result.restore_duration_seconds = (datetime.now() - start_time).total_seconds()
            result.success = True
            
            logger.info(f"Database restore completed from: {backup_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Restore failed for job {job_id}: {e}")
            result.add_error(str(e))
            
            # Ensure Neo4j is restarted
            try:
                await self.neo4j_service.start()
            except Exception as restart_error:
                logger.error(f"Failed to restart Neo4j after restore failure: {restart_error}")
            
            return result
    
    async def clear_database(self) -> BackupResult:
        """Clear the current Neo4j database completely."""
        
        result = BackupResult(job_id="clear_operation")
        
        try:
            logger.info("Clearing Neo4j database")
            
            # Stop Neo4j service
            stop_result = await self.neo4j_service.stop()
            if not stop_result.success:
                result.add_error(f"Failed to stop Neo4j: {stop_result.error}")
                return result
            
            # Remove database files
            if self.neo4j_data_dir.exists():
                shutil.rmtree(self.neo4j_data_dir)
                logger.info(f"Removed database directory: {self.neo4j_data_dir}")
            
            # Recreate empty database directory
            self.neo4j_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Restart Neo4j service
            start_result = await self.neo4j_service.start()
            if not start_result.success:
                result.add_error(f"Failed to restart Neo4j: {start_result.error}")
                return result
            
            result.success = True
            logger.info("Database cleared successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Database clear failed: {e}")
            result.add_error(str(e))
            
            # Ensure Neo4j is restarted
            try:
                await self.neo4j_service.start()
            except Exception:
                pass
            
            return result
    
    async def _find_backup_for_job(self, job_id: str) -> Optional[str]:
        """Find the most recent backup file for a given job ID."""
        
        try:
            # Look for backup files matching the job_id pattern
            pattern = f"neo4j_backup_{job_id}_*.tar.gz"
            matching_files = list(self.backup_storage_dir.glob(pattern))
            
            if not matching_files:
                return None
            
            # Return the most recent backup
            latest_backup = max(matching_files, key=lambda f: f.stat().st_mtime)
            return str(latest_backup)
            
        except Exception as e:
            logger.error(f"Error finding backup for job {job_id}: {e}")
            return None