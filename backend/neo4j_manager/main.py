#!/usr/bin/env python3
"""
Neo4j Database Manager - Handles database versioning and backup management

Manages Neo4j database lifecycle:
- Pre-upload backup creation with job_id naming
- Database clearing and restoration
- Backup location tracking and management
- Neo4j service lifecycle management
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .core.backup_manager import BackupManager
from .core.database_tracker import DatabaseTracker
from .services.backup_service import BackupService
from .models.backup_metadata import BackupMetadata

async def main():
    """Command-line entry point for Neo4j manager."""
    parser = argparse.ArgumentParser(
        description="Neo4j Database Manager - Handle database versioning"
    )
    parser.add_argument("--action", required=True, 
                       choices=["backup", "restore", "clear", "list"],
                       help="Action to perform")
    parser.add_argument("--job-id", help="Job ID for backup/restore operations")
    parser.add_argument("--backup-location", help="Custom backup location")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize services
    backup_manager = BackupManager()
    database_tracker = DatabaseTracker()
    backup_service = BackupService(backup_manager, database_tracker)
    
    try:
        if args.action == "backup":
            if not args.job_id:
                print("Job ID required for backup operation")
                sys.exit(1)
            
            backup_result = await backup_service.create_backup(args.job_id)
            if backup_result.success:
                print(f"Backup created: {backup_result.backup_path}")
                print(f"Job ID: {args.job_id}")
                sys.exit(0)
            else:
                print(f"Backup failed: {backup_result.error}")
                sys.exit(1)
        
        elif args.action == "restore":
            if not args.job_id:
                print("Job ID required for restore operation")
                sys.exit(1)
            
            restore_result = await backup_service.restore_backup(args.job_id)
            if restore_result.success:
                print(f"Database restored from: {restore_result.backup_path}")
                sys.exit(0)
            else:
                print(f"Restore failed: {restore_result.error}")
                sys.exit(1)
        
        elif args.action == "clear":
            clear_result = await backup_service.clear_database()
            if clear_result.success:
                print("Database cleared successfully")
                sys.exit(0)
            else:
                print(f"Clear failed: {clear_result.error}")
                sys.exit(1)
        
        elif args.action == "list":
            backups = await database_tracker.list_all_backups()
            print("Available database backups:")
            for backup in backups:
                print(f"  Job ID: {backup.job_id}")
                print(f"  Created: {backup.created_at}")
                print(f"  Location: {backup.backup_path}")
                print(f"  Size: {backup.size_mb:.2f} MB")
                print("  ---")
    
    except Exception as e:
        print(f"Manager operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())