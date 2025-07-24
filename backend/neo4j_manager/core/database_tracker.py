"""
Database Tracker - Manages job ID to backup location mapping

Tracks database backups, versions, and provides lookup functionality.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models.backup_metadata import BackupMetadata
from ..models.database_version import BackupRegistry, VersionHistory, DatabaseVersion

logger = logging.getLogger(__name__)


class DatabaseTracker:
    """Tracks database backups and versions."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        # Initialize from config if not provided
        if not storage_dir:
            from config import get_settings
            settings = get_settings()
            storage_dir = settings.database.neo4j_backup_dir
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.registry_file = self.storage_dir / "backup_registry.json"
        self.version_history_file = self.storage_dir / "version_history.json"
        
        # Load existing data
        self.backup_registry = self._load_backup_registry()
        self.version_history = self._load_version_history()
    
    async def register_backup(self, job_id: str, backup_path: str, **metadata) -> BackupMetadata:
        """Register a new backup with the tracker."""
        
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create backup metadata
            backup_metadata = BackupMetadata(
                job_id=job_id,
                backup_path=backup_path,
                size_bytes=backup_file.stat().st_size,
                description=metadata.get("description"),
                neo4j_version=metadata.get("neo4j_version"),
                node_count=metadata.get("node_count"),
                relationship_count=metadata.get("relationship_count")
            )
            
            # Register in backup registry
            self.backup_registry.register_backup(backup_metadata)
            
            # Save registry
            await self._save_backup_registry()
            
            logger.info(f"Registered backup for job {job_id}: {backup_path}")
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Failed to register backup for job {job_id}: {e}")
            raise
    
    async def add_database_version(
        self, 
        job_id: str, 
        backup_path: Optional[str] = None,
        **version_metadata
    ) -> DatabaseVersion:
        """Add a new database version to the history."""
        
        try:
            # Create database version
            version = DatabaseVersion(
                job_id=job_id,
                backup_path=backup_path,
                source_codebase=version_metadata.get("source_codebase"),
                extraction_job_id=version_metadata.get("extraction_job_id"),
                transformation_job_id=version_metadata.get("transformation_job_id"),
                description=version_metadata.get("description"),
                node_count=version_metadata.get("node_count"),
                relationship_count=version_metadata.get("relationship_count"),
                property_count=version_metadata.get("property_count"),
                tags=version_metadata.get("tags", [])
            )
            
            # Add to version history
            self.version_history.add_version(version)
            
            # Save version history
            await self._save_version_history()
            
            logger.info(f"Added database version for job {job_id}: v{version.version_number}")
            return version
            
        except Exception as e:
            logger.error(f"Failed to add database version for job {job_id}: {e}")
            raise
    
    async def get_backup_by_job_id(self, job_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata by job ID."""
        return self.backup_registry.get_backup(job_id)
    
    async def list_all_backups(
        self, 
        include_missing: bool = False,
        max_age_days: Optional[int] = None
    ) -> List[BackupMetadata]:
        """List all registered backups."""
        return self.backup_registry.list_backups(include_missing, max_age_days)
    
    async def get_database_version_by_job_id(self, job_id: str) -> Optional[DatabaseVersion]:
        """Get database version by job ID."""
        return self.version_history.get_version_by_job_id(job_id)
    
    async def get_current_database_version(self) -> Optional[DatabaseVersion]:
        """Get the currently active database version."""
        return self.version_history.get_active_version()
    
    async def list_database_versions(self, limit: Optional[int] = None) -> List[DatabaseVersion]:
        """List database versions."""
        return self.version_history.list_versions(limit)
    
    async def cleanup_missing_backups(self) -> List[str]:
        """Remove entries for backups that no longer exist."""
        removed = self.backup_registry.cleanup_missing()
        if removed:
            await self._save_backup_registry()
            logger.info(f"Cleaned up {len(removed)} missing backups: {removed}")
        return removed
    
    async def delete_backup(self, job_id: str) -> bool:
        """Delete a backup and its registry entry."""
        try:
            backup = await self.get_backup_by_job_id(job_id)
            if not backup:
                return False
            
            # Remove physical file
            backup_file = Path(backup.backup_path)
            if backup_file.exists():
                backup_file.unlink()
            
            # Remove from registry
            if job_id in self.backup_registry.backups:
                del self.backup_registry.backups[job_id]
                await self._save_backup_registry()
            
            logger.info(f"Deleted backup for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup for job {job_id}: {e}")
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            "total_backups": len(self.backup_registry.backups),
            "total_size_mb": self.backup_registry.get_total_size_mb(),
            "total_versions": len(self.version_history.versions),
            "current_version": self.version_history.current_version,
            "storage_directory": str(self.storage_dir)
        }
        
        # Add age distribution
        backups = await self.list_all_backups()
        if backups:
            ages = [backup.age_days for backup in backups]
            stats["oldest_backup_days"] = max(ages)
            stats["newest_backup_days"] = min(ages)
            stats["average_backup_age_days"] = sum(ages) / len(ages)
        
        return stats
    
    def _load_backup_registry(self) -> BackupRegistry:
        """Load backup registry from file."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                # Convert dictionary data back to BackupRegistry
                registry = BackupRegistry()
                for job_id, backup_data in data.get("backups", {}).items():
                    backup_metadata = BackupMetadata(
                        job_id=backup_data["job_id"],
                        backup_path=backup_data["backup_path"],
                        created_at=datetime.fromisoformat(backup_data["created_at"]),
                        size_bytes=backup_data["size_bytes"],
                        description=backup_data.get("description"),
                        neo4j_version=backup_data.get("neo4j_version"),
                        node_count=backup_data.get("node_count"),
                        relationship_count=backup_data.get("relationship_count")
                    )
                    registry.register_backup(backup_metadata)
                
                return registry
        except Exception as e:
            logger.warning(f"Failed to load backup registry: {e}")
        
        return BackupRegistry()
    
    def _load_version_history(self) -> VersionHistory:
        """Load version history from file."""
        try:
            if self.version_history_file.exists():
                with open(self.version_history_file, 'r') as f:
                    data = json.load(f)
                
                # Convert dictionary data back to VersionHistory
                history = VersionHistory()
                for version_data in data.get("versions", []):
                    version = DatabaseVersion(
                        job_id=version_data["job_id"],
                        version_number=version_data["version_number"],
                        created_at=datetime.fromisoformat(version_data["created_at"]),
                        backup_path=version_data.get("backup_path"),
                        is_active=version_data.get("is_active", False),
                        node_count=version_data.get("node_count"),
                        relationship_count=version_data.get("relationship_count"),
                        property_count=version_data.get("property_count"),
                        source_codebase=version_data.get("source_codebase"),
                        extraction_job_id=version_data.get("extraction_job_id"),
                        transformation_job_id=version_data.get("transformation_job_id"),
                        description=version_data.get("description"),
                        tags=version_data.get("tags", [])
                    )
                    history.versions.append(version)
                
                history.current_version = data.get("current_version")
                return history
        except Exception as e:
            logger.warning(f"Failed to load version history: {e}")
        
        return VersionHistory()
    
    async def _save_backup_registry(self) -> None:
        """Save backup registry to file."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.backup_registry.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup registry: {e}")
            raise
    
    async def _save_version_history(self) -> None:
        """Save version history to file."""
        try:
            with open(self.version_history_file, 'w') as f:
                json.dump(self.version_history.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save version history: {e}")
            raise