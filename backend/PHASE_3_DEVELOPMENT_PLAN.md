# Phase 3 Development Plan: Neo4j Upload & Integration

## Executive Summary

This document provides a comprehensive technical specification for Phase 3 development, which focuses on uploading Phase 2 transformation results to Neo4j graph database. Based on extensive analysis of the existing backend architecture, this plan leverages robust Neo4j utilities already present in the codebase while maintaining consistency with established patterns from Phases 1 and 2.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Existing Component Analysis](#existing-component-analysis)
3. [Phase 3 Technical Specification](#phase-3-technical-specification)
4. [API Integration Plan](#api-integration-plan)
5. [UI Integration Strategy](#ui-integration-strategy)
6. [Implementation Roadmap](#implementation-roadmap)
7. [Error Handling & Recovery](#error-handling--recovery)
8. [Testing Strategy](#testing-strategy)
9. [Performance Considerations](#performance-considerations)
10. [Security & Configuration](#security--configuration)

---

## Architecture Overview

### Current System Architecture

The backend follows a well-structured, domain-separated architecture:

```
/backend/
├── api/                      # FastAPI REST endpoints
├── config.py                 # Centralized configuration management
├── transformer/              # Phase 2: Transformation Domain ✅ COMPLETED
├── graph_builder/            # Neo4j relationship extraction utilities
├── parser/                   # Phase 1: Extraction components
│   ├── dev/                  # Development parser components  
│   ├── prod/                 # Production parser components
│   ├── exporters/            # Database export utilities
│   └── plugins/              # Parser plugin system
└── version_manager/          # Version control utilities
```

### Phase 3 Integration Point

Phase 3 will integrate seamlessly into the existing pipeline with database versioning:

```
Phase 1: Raw Code → Structured JSON
Phase 2: JSON → Neo4j Tuples + Cypher Commands  
Phase 3: Neo4j Manager + Upload → Versioned Neo4j Database ⬅ NEW PHASES
```

**Critical Constraint:** Neo4j instance can only handle one database at a time, requiring:
- Database backup before each upload
- Complete database clearing and recreation
- Version management with job_id-based backups

---

## Existing Component Analysis

### 1. Neo4j Utilities Already Available

#### **A. Neo4j Exporter (`parser/exporters/neo4j_exporter.py`)**

**Capabilities:**
- ✅ Full Neo4j connection management with authentication
- ✅ Batch transaction processing (configurable batch size: default 100)
- ✅ Schema introspection and validation
- ✅ Comprehensive error handling with connection retry
- ✅ Node and relationship creation with proper labeling
- ✅ Architectural pattern detection
- ✅ Plugin-based registration system

**Key Features:**
```python
class Neo4jExporter(ParserExporter):
    def __init__(self, options):
        # Environment-based configuration
        default_options = {
            "uri": os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.environ.get("NEO4J_USER", "neo4j"),
            "password": os.environ.get("NEO4J_PASSWORD", "password"),
            "database": os.environ.get("NEO4J_DATABASE", "neo4j"),
            "batch_size": 100,
            "clear_existing": False,
            "relationship_types": ["IMPORTS", "DEFINES", "CONTAINS", "CALLS", "INHERITS_FROM", "DEPENDS_ON"]
        }
```

**Strength Analysis:**
- 🎯 **Production Ready**: Handles connection pooling, retries, and batch processing
- 🎯 **Configurable**: Environment-based configuration with sensible defaults
- 🎯 **Comprehensive**: Supports all major relationship types and node creation
- 🎯 **Error Resilient**: Proper exception handling and transaction management

#### **B. Relationship Extractor (`graph_builder/relationship_extractor.py`)**

**Capabilities:**
- ✅ Advanced AST-based relationship extraction (adapted from MCP components)
- ✅ Multiple relationship types: imports, function calls, method calls, inheritance, class usage
- ✅ Dual storage: PostgreSQL for metadata + Neo4j for graph relationships
- ✅ Parameterized Cypher query generation with proper escaping
- ✅ Batch relationship processing

**Key Features:**
```python
class RelationshipExtractor(ast.NodeVisitor):
    def __init__(self, file_path, module_name, postgres_client=None, neo4j_client=None):
        # Dependency injection pattern for database clients
        
    def create_neo4j_relationships(self) -> bool:
        # Generates parameterized Cypher queries for each relationship type
        for rel in self.relationships:
            if rel.relationship_type == 'import':
                query = self._generate_import_cypher(rel)
            elif rel.relationship_type == 'function_call':
                query = self._generate_function_call_cypher(rel)
            # ... handles all relationship types
```

**Strength Analysis:**
- 🎯 **Sophisticated**: Advanced AST parsing with comprehensive relationship detection
- 🎯 **Dual Storage**: PostgreSQL + Neo4j integration pattern
- 🎯 **Parameterized Queries**: SQL injection safe with escaping
- 🎯 **Extensible**: Plugin architecture for new relationship types

#### **C. Neo4j Formatter (`transformer/formatters/neo4j_formatter.py`)**

**Capabilities:**
- ✅ Production-ready Cypher command generation
- ✅ Parameterized queries with proper escaping
- ✅ Safe literal query generation for manual execution
- ✅ Batch execution scripts
- ✅ Comprehensive metadata tracking

**Key Features:**
```python
class Neo4jFormatter:
    def format(self, tuple_set: TupleSet) -> str:
        # Generates production-ready Cypher commands
        
    def format_parameterized(self, tuple_set: TupleSet) -> List[Dict]:
        # Generates parameterized queries for batch execution
```

**Strength Analysis:**
- 🎯 **Safe Execution**: Parameterized queries prevent injection attacks
- 🎯 **Batch Optimized**: Designed for efficient bulk operations
- 🎯 **Metadata Rich**: Comprehensive tracking and logging
- 🎯 **Formatter Plugin**: Follows established plugin patterns

### 2. Configuration Management (`config.py`)

**Existing Neo4j Configuration:**
```python
class DatabaseSettings(BaseSettings):
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username") 
    neo4j_password: str = Field(default="password", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

def get_neo4j_config(self) -> dict:
    return {
        "uri": self.database.neo4j_uri,
        "auth": (self.database.neo4j_user, self.database.neo4j_password),
        "database": self.database.neo4j_database,
    }
```

**Strength Analysis:**
- 🎯 **Environment Driven**: Proper separation of configuration from code
- 🎯 **Type Safe**: Pydantic models with validation
- 🎯 **Centralized**: Single source of truth for all database settings
- 🎯 **Ready for Extension**: Easy to add Phase 3 specific settings

### 3. Phase 1 & Phase 2 Integration Patterns

#### **Data Flow Architecture:**
```
Phase 1: main.py → StatusReporter → Job tracking → File output
Phase 2: main.py → transform_file() → Job tracking → Dual file output  
Phase 3: main.py → upload_to_neo4j() → Job tracking → Upload results
```

#### **Common Patterns:**
- ✅ **CLI Interface**: `argparse` with `--job-id`, `--input`, `--output` parameters
- ✅ **Async/Await**: Non-blocking execution with `asyncio`
- ✅ **Background Tasks**: FastAPI `BackgroundTasks` for long-running operations
- ✅ **Progress Reporting**: Real-time updates via orchestrator communication
- ✅ **Error Handling**: Structured error collection and reporting
- ✅ **File Naming**: Consistent job_id inclusion in all output files

---

## Phase 3 Technical Specification

### 1. Domain Structure

**Recommended Phase 3 Directory Layout:**
```
/backend/
├── neo4j_manager/               # NEW: Neo4j Database Version Management
│   ├── __init__.py             # Domain initialization
│   ├── main.py                 # Database manager CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── backup_manager.py   # Database backup/restore operations
│   │   ├── tarball_manager.py  # Tarball creation and management
│   │   ├── database_tracker.py # Job ID to database mapping
│   │   └── neo4j_service.py    # Neo4j service control (start/stop)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── backup_service.py   # Automated backup workflows
│   │   ├── restore_service.py  # Database restoration workflows
│   │   └── cleanup_service.py  # Old backup cleanup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── backup_metadata.py  # Backup information models
│   │   └── database_version.py # Database version tracking
│   └── storage/
│       ├── __init__.py
│       └── backup_registry.py  # Backup location registry
├── uploader/                    # Phase 3 Upload Domain
│   ├── __init__.py             # Domain initialization
│   ├── main.py                 # Upload orchestrator (CLI entry point)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── neo4j_client.py     # Enhanced Neo4j client wrapper
│   │   ├── batch_uploader.py   # Bulk upload operations
│   │   ├── transaction_manager.py  # Transaction management & rollback
│   │   └── progress_tracker.py # Upload progress tracking
│   ├── services/
│   │   ├── __init__.py
│   │   ├── connection_service.py   # Connection pool management
│   │   ├── validation_service.py  # Pre-upload validation
│   │   └── retry_service.py        # Retry and error handling
│   ├── models/
│   │   ├── __init__.py
│   │   ├── upload_result.py    # Upload result models
│   │   └── upload_metadata.py  # Upload metadata models
│   └── formatters/
│       ├── __init__.py
│       └── cypher_executor.py  # Execute Cypher commands safely
```

### 2. Core Components Design

#### **A. Neo4j Manager (`neo4j_manager/main.py`)**

**Purpose:** Manages Neo4j database versioning, backup, and restoration to handle the single-database constraint.

**Key Responsibilities:**
- Create database backups before each upload
- Manage tarball creation with job_id naming
- Track job_id to backup location mapping
- Provide database restoration capabilities
- Handle Neo4j service lifecycle (stop/start for backups)

```python
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
```

#### **B. Backup Manager (`neo4j_manager/core/backup_manager.py`)**

**Purpose:** Core backup and restore operations for Neo4j database files.

```python
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
        backup_storage_dir: Optional[str] = None
    ):
        # Initialize from config if not provided
        if not neo4j_data_dir or not backup_storage_dir:
            from backend.config import get_settings
            settings = get_settings()
            
            # Add these to config.py neo4j settings
            self.neo4j_data_dir = Path(neo4j_data_dir or "/var/lib/neo4j/data")
            self.backup_storage_dir = Path(backup_storage_dir or "./neo4j_backups")
        else:
            self.neo4j_data_dir = Path(neo4j_data_dir)
            self.backup_storage_dir = Path(backup_storage_dir)
        
        # Ensure backup directory exists
        self.backup_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Services
        self.neo4j_service = Neo4jService()
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
```

#### **C. Upload Orchestrator (`uploader/main.py`)**

**Purpose:** CLI entry point that integrates with the existing orchestrator pipeline.

```python
#!/usr/bin/env python3
"""
Phase 3 Upload Orchestrator - CLI Interface

Uploads Phase 2 transformation results to Neo4j graph database.
Integrates with existing orchestrator pipeline via CLI interface.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .core.neo4j_client import Neo4jClient
from .core.batch_uploader import BatchUploader
from .services.validation_service import ValidationService
from .models.upload_result import UploadResult

async def main():
    """Command-line entry point for uploader."""
    parser = argparse.ArgumentParser(
        description="Upload Phase 2 transformation results to Neo4j"
    )
    parser.add_argument("--input", required=True, help="Path to cypher_commands file")
    parser.add_argument("--job-id", required=True, help="Job identifier")
    parser.add_argument("--neo4j-uri", help="Neo4j connection URI")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploads")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't upload")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize services
    neo4j_client = Neo4jClient(uri=args.neo4j_uri)
    validator = ValidationService()
    uploader = BatchUploader(neo4j_client, batch_size=args.batch_size)
    
    try:
        # Validate input file
        validation_result = await validator.validate_cypher_file(args.input)
        if not validation_result.is_valid:
            print(f"Validation failed: {validation_result.errors}")
            sys.exit(1)
        
        if args.validate_only:
            print("Validation successful")
            sys.exit(0)
        
        # Perform upload
        upload_result = await uploader.upload_from_file(
            args.input, 
            job_id=args.job_id
        )
        
        if upload_result.success:
            print(f"Upload successful. Job ID: {upload_result.job_id}")
            print(f"Uploaded: {upload_result.nodes_created} nodes, {upload_result.relationships_created} relationships")
            sys.exit(0)
        else:
            print(f"Upload failed: {', '.join(upload_result.errors)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

#### **B. Enhanced Neo4j Client (`uploader/core/neo4j_client.py`)**

**Purpose:** Production-ready Neo4j client with connection pooling, health monitoring, and retry logic.

```python
"""
Enhanced Neo4j Client for Phase 3 Upload Operations

Provides production-ready Neo4j connectivity with:
- Connection pooling and health monitoring
- Automatic retry logic with exponential backoff
- Transaction management with rollback support  
- Comprehensive error handling and logging
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from neo4j import GraphDatabase, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from ..models.upload_result import UploadResult, ConnectionHealth
from ..services.retry_service import RetryService

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Enhanced Neo4j client for Phase 3 upload operations."""
    
    def __init__(
        self, 
        uri: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 100,
        connection_acquisition_timeout: int = 60
    ):
        # Initialize from config if not provided
        if not uri or not auth:
            from backend.config import get_settings
            settings = get_settings()
            neo4j_config = settings.get_neo4j_config()
            
            self.uri = uri or neo4j_config["uri"]
            self.auth = auth or neo4j_config["auth"]
            self.database = database or neo4j_config["database"]
        else:
            self.uri = uri
            self.auth = auth
            self.database = database
        
        # Connection pool configuration
        self.driver = None
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_acquisition_timeout = connection_acquisition_timeout
        
        # Health monitoring
        self.last_health_check = None
        self.health_check_interval = timedelta(minutes=5)
        
        # Retry service
        self.retry_service = RetryService()
        
        # Statistics
        self.connection_stats = {
            "total_connections": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_upload_time": 0,
            "last_upload": None
        }
    
    async def connect(self) -> bool:
        """Establish connection to Neo4j with health validation."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=self.auth,
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout
            )
            
            # Verify connectivity
            await self._verify_connectivity()
            
            logger.info(f"Connected to Neo4j at {self.uri}")
            self.connection_stats["total_connections"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    async def health_check(self) -> ConnectionHealth:
        """Perform comprehensive health check."""
        try:
            # Check if health check is needed
            now = datetime.now()
            if (self.last_health_check and 
                now - self.last_health_check < self.health_check_interval):
                return ConnectionHealth(healthy=True, last_check=self.last_health_check)
            
            if not self.driver:
                await self.connect()
            
            # Test query execution
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as test")
                await result.consume()
            
            self.last_health_check = now
            return ConnectionHealth(
                healthy=True,
                last_check=now,
                response_time_ms=0,  # Could measure actual response time
                database_version=await self._get_database_version()
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ConnectionHealth(
                healthy=False,
                last_check=now,
                error=str(e)
            )
    
    async def execute_cypher_batch(
        self, 
        cypher_commands: List[str],
        batch_size: int = 100,
        job_id: Optional[str] = None
    ) -> UploadResult:
        """Execute Cypher commands in optimized batches."""
        
        result = UploadResult(job_id=job_id or "unknown")
        start_time = datetime.now()
        
        try:
            if not self.driver:
                if not await self.connect():
                    result.add_error("Failed to connect to Neo4j")
                    return result
            
            # Health check before upload
            health = await self.health_check()
            if not health.healthy:
                result.add_error(f"Database health check failed: {health.error}")
                return result
            
            # Process commands in batches
            total_commands = len(cypher_commands)
            processed = 0
            
            for i in range(0, total_commands, batch_size):
                batch = cypher_commands[i:i + batch_size]
                
                batch_result = await self._execute_batch_with_retry(batch, job_id)
                result.merge_stats(batch_result)
                
                processed += len(batch)
                
                # Report progress (could integrate with progress service)
                progress = (processed / total_commands) * 100
                logger.info(f"Upload progress: {progress:.1f}% ({processed}/{total_commands})")
            
            # Update final statistics
            end_time = datetime.now()
            upload_duration = (end_time - start_time).total_seconds()
            
            result.upload_duration_seconds = upload_duration
            result.total_commands_executed = processed
            
            self.connection_stats["successful_queries"] += processed
            self.connection_stats["total_upload_time"] += upload_duration
            self.connection_stats["last_upload"] = end_time
            
            if not result.has_errors:
                logger.info(f"Upload completed successfully in {upload_duration:.2f}s")
                logger.info(f"Created {result.nodes_created} nodes, {result.relationships_created} relationships")
            
            return result
            
        except Exception as e:
            logger.error(f"Batch upload failed: {e}")
            result.add_error(str(e))
            self.connection_stats["failed_queries"] += 1
            return result
    
    async def _execute_batch_with_retry(
        self, 
        batch: List[str], 
        job_id: Optional[str]
    ) -> UploadResult:
        """Execute a single batch with retry logic."""
        
        async def execute_batch():
            batch_result = UploadResult(job_id=job_id)
            
            async with self.driver.session(database=self.database) as session:
                async with session.begin_transaction() as tx:
                    for command in batch:
                        try:
                            result = await tx.run(command)
                            summary = await result.consume()
                            
                            # Update statistics from summary
                            batch_result.nodes_created += summary.counters.nodes_created
                            batch_result.relationships_created += summary.counters.relationships_created
                            batch_result.properties_set += summary.counters.properties_set
                            
                        except Exception as e:
                            logger.error(f"Command failed: {command[:100]}... Error: {e}")
                            batch_result.add_error(f"Command failed: {str(e)}")
                            # Continue with other commands in batch
            
            return batch_result
        
        return await self.retry_service.execute_with_retry(
            execute_batch,
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        )
    
    async def _verify_connectivity(self) -> None:
        """Verify database connectivity with detailed error reporting."""
        try:
            self.driver.verify_connectivity()
        except ServiceUnavailable as e:
            raise ConnectionError(f"Neo4j service unavailable: {e}")
        except AuthError as e:
            raise ConnectionError(f"Neo4j authentication failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Neo4j connection failed: {e}")
    
    async def _get_database_version(self) -> Optional[str]:
        """Get Neo4j database version."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
                record = await result.single()
                if record:
                    return f"{record['name']} {record['versions'][0]}"
            return None
        except Exception:
            return None
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection and performance statistics."""
        return self.connection_stats.copy()
```

#### **C. Batch Uploader (`uploader/core/batch_uploader.py`)**

**Purpose:** Optimized batch processing with memory management and progress tracking.

```python
"""
Batch Uploader for Neo4j - Optimized bulk upload operations

Handles large-scale uploads with:
- Memory-efficient streaming processing
- Progress tracking and reporting
- Error recovery and partial upload support
- Transaction management with rollback
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from pathlib import Path
from datetime import datetime

from .neo4j_client import Neo4jClient
from .progress_tracker import ProgressTracker
from ..services.validation_service import ValidationService
from ..models.upload_result import UploadResult, BatchResult

logger = logging.getLogger(__name__)

class BatchUploader:
    """Optimized batch uploader for Neo4j operations."""
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        batch_size: int = 100,
        max_memory_mb: int = 500,
        enable_progress_tracking: bool = True
    ):
        self.neo4j_client = neo4j_client
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        
        # Services
        self.validator = ValidationService()
        
        if enable_progress_tracking:
            self.progress_tracker = ProgressTracker()
        else:
            self.progress_tracker = None
    
    async def upload_from_file(
        self, 
        cypher_file_path: str, 
        job_id: str,
        validate_before_upload: bool = True
    ) -> UploadResult:
        """Upload Cypher commands from file with validation and progress tracking."""
        
        result = UploadResult(job_id=job_id)
        
        try:
            cypher_path = Path(cypher_file_path)
            if not cypher_path.exists():
                result.add_error(f"Cypher file not found: {cypher_file_path}")
                return result
            
            # Validate file before upload
            if validate_before_upload:
                validation_result = await self.validator.validate_cypher_file(cypher_file_path)
                if not validation_result.is_valid:
                    result.add_error(f"Validation failed: {validation_result.errors}")
                    return result
                
                result.total_commands = validation_result.total_commands
                result.estimated_nodes = validation_result.estimated_nodes
                result.estimated_relationships = validation_result.estimated_relationships
            
            # Start progress tracking
            if self.progress_tracker:
                await self.progress_tracker.start_upload(job_id, result.total_commands)
            
            # Stream and upload in batches
            async for batch_result in self._stream_upload_batches(cypher_file_path, job_id):
                result.merge_batch_result(batch_result)
                
                # Update progress
                if self.progress_tracker:
                    await self.progress_tracker.update_progress(
                        result.total_commands_executed,
                        result.total_commands
                    )
            
            # Complete progress tracking
            if self.progress_tracker:
                await self.progress_tracker.complete_upload(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Upload from file failed: {e}")
            result.add_error(str(e))
            
            if self.progress_tracker:
                await self.progress_tracker.report_error(str(e))
            
            return result
    
    async def upload_from_commands(
        self,
        cypher_commands: List[str],
        job_id: str
    ) -> UploadResult:
        """Upload Cypher commands directly from list."""
        
        result = UploadResult(job_id=job_id)
        result.total_commands = len(cypher_commands)
        
        try:
            # Start progress tracking
            if self.progress_tracker:
                await self.progress_tracker.start_upload(job_id, len(cypher_commands))
            
            # Process in batches
            for i in range(0, len(cypher_commands), self.batch_size):
                batch = cypher_commands[i:i + self.batch_size]
                
                batch_result = await self.neo4j_client.execute_cypher_batch(
                    batch, 
                    batch_size=self.batch_size,
                    job_id=job_id
                )
                
                result.merge_batch_result(batch_result)
                
                # Update progress
                if self.progress_tracker:
                    await self.progress_tracker.update_progress(
                        result.total_commands_executed,
                        result.total_commands
                    )
            
            # Complete progress tracking
            if self.progress_tracker:
                await self.progress_tracker.complete_upload(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Upload from commands failed: {e}")
            result.add_error(str(e))
            
            if self.progress_tracker:
                await self.progress_tracker.report_error(str(e))
            
            return result
    
    async def _stream_upload_batches(
        self, 
        cypher_file_path: str, 
        job_id: str
    ) -> AsyncIterator[BatchResult]:
        """Stream Cypher commands from file and upload in batches."""
        
        current_batch = []
        batch_number = 1
        
        async for command in self._stream_cypher_commands(cypher_file_path):
            current_batch.append(command)
            
            if len(current_batch) >= self.batch_size:
                # Upload current batch
                batch_result = await self._upload_single_batch(
                    current_batch, 
                    batch_number, 
                    job_id
                )
                yield batch_result
                
                # Reset for next batch
                current_batch = []
                batch_number += 1
        
        # Upload final batch if it has commands
        if current_batch:
            batch_result = await self._upload_single_batch(
                current_batch, 
                batch_number, 
                job_id
            )
            yield batch_result
    
    async def _stream_cypher_commands(
        self, 
        cypher_file_path: str
    ) -> AsyncIterator[str]:
        """Stream Cypher commands from file for memory-efficient processing."""
        
        with open(cypher_file_path, 'r', encoding='utf-8') as f:
            current_command = []
            
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('//'):
                    continue
                
                current_command.append(line)
                
                # Check if command is complete (ends with semicolon)
                if line.endswith(';'):
                    command = ' '.join(current_command)
                    yield command
                    current_command = []
            
            # Handle final command without semicolon
            if current_command:
                command = ' '.join(current_command)
                if command.strip():
                    yield command
    
    async def _upload_single_batch(
        self, 
        batch_commands: List[str], 
        batch_number: int, 
        job_id: str
    ) -> BatchResult:
        """Upload a single batch with detailed result tracking."""
        
        batch_result = BatchResult(
            batch_number=batch_number,
            job_id=job_id,
            commands_in_batch=len(batch_commands)
        )
        
        start_time = datetime.now()
        
        try:
            upload_result = await self.neo4j_client.execute_cypher_batch(
                batch_commands,
                batch_size=len(batch_commands),
                job_id=job_id
            )
            
            # Copy statistics
            batch_result.nodes_created = upload_result.nodes_created
            batch_result.relationships_created = upload_result.relationships_created
            batch_result.properties_set = upload_result.properties_set
            batch_result.errors.extend(upload_result.errors)
            
            batch_result.success = not upload_result.has_errors
            
        except Exception as e:
            logger.error(f"Batch {batch_number} upload failed: {e}")
            batch_result.add_error(str(e))
            batch_result.success = False
        
        batch_result.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Batch {batch_number}: {batch_result.commands_in_batch} commands, "
                   f"{batch_result.nodes_created} nodes, {batch_result.relationships_created} relationships, "
                   f"{batch_result.execution_time_seconds:.2f}s")
        
        return batch_result
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """Get uploader performance statistics."""
        stats = {
            "batch_size": self.batch_size,
            "max_memory_mb": self.max_memory_mb,
        }
        
        if hasattr(self, 'neo4j_client'):
            stats.update(self.neo4j_client.get_connection_stats())
        
        return stats
```

### 3. Integration with Orchestrator Pipeline

#### **Orchestrator Updates (`parser/prod/orchestrator/main.py`)**

**Required Changes with Neo4j Manager Integration:**
```python
# Add Phase 3 configuration to Job class
class Job:
    def __init__(self, job_id: str, codebase_path: str):
        # ... existing fields ...
        
        # Phase 3 output files
        self.backup_result = None    # Path to backup result file
        self.upload_result = None    # Path to upload result file
        self.neo4j_stats = None      # Upload statistics

# Update pipeline to include Phase 3 with backup management
async def run_pipeline(self, job_id: str) -> None:
    try:
        # ... Phase 1 and Phase 2 execution ...
        
        # Phase 3a: Backup current database
        self.update_job_status(
            job_id,
            JobStatus.LOADING,
            "backup",
            "Creating database backup"
        )
        
        backup_result = await self._run_neo4j_backup(job)
        job.backup_result = backup_result
        
        # Phase 3b: Upload to Neo4j
        self.update_job_status(
            job_id,
            JobStatus.LOADING,
            "loading",
            "Uploading to Neo4j database"
        )
        
        upload_result = await self._run_uploader(job)
        job.upload_result = upload_result
        
        # Mark as completed
        self.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            "completed", 
            "Pipeline completed successfully",
            progress=100.0
        )
        
    except Exception as e:
        # ... existing error handling ...

async def _run_neo4j_backup(self, job: Job) -> str:
    """Run the Neo4j backup phase before upload."""
    
    backup_result_file = f"backup_result_{job.job_id}.json"
    
    cmd = [
        sys.executable,
        str(self.neo4j_manager_dir / "main.py"),
        "--action", "backup",
        "--job-id", job.job_id
    ]
    
    logger.info(f"Running Neo4j backup: {' '.join(cmd)}")
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        self.executor,
        subprocess.run,
        cmd,
        subprocess.PIPE,
        subprocess.PIPE,
        True  # capture_output
    )
    
    if result.returncode != 0:
        logger.warning(f"Backup failed: {result.stderr.decode()}")
        # Continue with upload even if backup fails
        # In production, you might want to make this configurable
    
    return backup_result_file

async def _run_uploader(self, job: Job) -> str:
    """Run the uploader phase with integrated backup management."""
    
    # Ensure we have cypher commands from Phase 2
    if not job.cypher_commands or not Path(job.cypher_commands).exists():
        raise RuntimeError("Phase 2 output not found - cannot proceed with upload")
    
    upload_result_file = f"upload_result_{job.job_id}.json"
    
    cmd = [
        sys.executable,
        str(self.uploader_dir / "main.py"),
        "--input", job.cypher_commands,
        "--job-id", job.job_id,
        "--output", upload_result_file,
        "--clear-database", "true"  # Always clear before upload
    ]
    
    logger.info(f"Running uploader: {' '.join(cmd)}")
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        self.executor,
        subprocess.run,
        cmd,
        subprocess.PIPE,
        subprocess.PIPE,
        True  # capture_output
    )
    
    if result.returncode != 0:
        # If upload fails, offer to restore backup
        logger.error(f"Upload failed: {result.stderr.decode()}")
        
        if job.backup_result:
            logger.info("Upload failed - backup available for restoration")
            # Could trigger automatic restore here or leave for manual operation
        
        raise RuntimeError(f"Uploader failed: {result.stderr.decode()}")
    
    return upload_result_file

# Add directory for Neo4j Manager
def __init__(self):
    # ... existing initialization ...
    self.neo4j_manager_dir = self.base_dir / "neo4j_manager"
```

**Complete Phase 3 Workflow:**
```
1. Phase 1: Extract code → extraction_output_{job_id}.json
2. Phase 2: Transform → cypher_commands_{job_id}.cypher + tuples_{job_id}.json
3. Phase 3a: Backup current Neo4j → neo4j_backup_{job_id}_{timestamp}.tar.gz
4. Phase 3b: Clear database → Empty Neo4j instance
5. Phase 3c: Upload new data → Upload statistics and results
6. Complete: Update job status → All files available for download
```

---

## API Integration Plan

### 1. Enhanced Endpoints with Backup Management

#### **A. Backup Management Endpoints**

```python
@app.get("/v1/jobs/{job_id}/backup-status")
async def get_backup_status(job_id: str) -> Dict[str, Any]:
    """Get backup status for a specific job."""
    
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    # Load backup result if available
    backup_info = None
    if job.backup_result and Path(job.backup_result).exists():
        with open(job.backup_result, 'r') as f:
            backup_info = json.load(f)
    
    return {
        "job_id": job_id,
        "backup_completed": bool(backup_info),
        "backup_info": backup_info,
        "can_restore": bool(backup_info and backup_info.get("backup_path"))
    }

@app.get("/v1/backups")
async def list_all_backups() -> Dict[str, Any]:
    """List all available database backups."""
    
    # Use Neo4j Manager to get backup list
    from backend.neo4j_manager.core.database_tracker import DatabaseTracker
    
    tracker = DatabaseTracker()
    backups = await tracker.list_all_backups()
    
    return {
        "backups": [
            {
                "job_id": backup.job_id,
                "created_at": backup.created_at.isoformat(),
                "backup_path": backup.backup_path,
                "size_mb": backup.size_mb,
                "description": backup.description or f"Backup for job {backup.job_id}"
            }
            for backup in backups
        ],
        "total_backups": len(backups)
    }

@app.post("/v1/backups/{job_id}/restore")
async def restore_backup(
    job_id: str, 
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """Restore Neo4j database from a specific backup."""
    
    # Check if backup exists
    from backend.neo4j_manager.core.database_tracker import DatabaseTracker
    
    tracker = DatabaseTracker()
    backup = await tracker.get_backup_by_job_id(job_id)
    
    if not backup:
        raise HTTPException(
            status_code=404,
            detail=f"No backup found for job ID: {job_id}"
        )
    
    # Trigger restore in background
    async def restore_task():
        from backend.neo4j_manager.services.restore_service import RestoreService
        restore_service = RestoreService()
        result = await restore_service.restore_backup(job_id)
        
        # Log result
        if result.success:
            logger.info(f"Backup restored successfully for job {job_id}")
        else:
            logger.error(f"Backup restore failed for job {job_id}: {result.error}")
    
    background_tasks.add_task(restore_task)
    
    return {
        "job_id": job_id,
        "message": "Backup restore initiated",
        "backup_path": backup.backup_path
    }

@app.delete("/v1/backups/{job_id}")
async def delete_backup(job_id: str) -> Dict[str, str]:
    """Delete a specific backup."""
    
    from backend.neo4j_manager.services.cleanup_service import CleanupService
    
    cleanup_service = CleanupService()
    result = await cleanup_service.delete_backup(job_id)
    
    if result.success:
        return {
            "job_id": job_id,
            "message": "Backup deleted successfully"
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to delete backup: {result.error}"
        )
```

#### **B. Upload Status Endpoint**
```python
@app.get("/v1/jobs/{job_id}/upload-status")
async def get_upload_status(job_id: str) -> Dict[str, Any]:
    """Get detailed Neo4j upload status."""
    
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
        "status": job.status,
        "upload_completed": job.status == JobStatus.COMPLETED,
        "upload_stats": upload_stats,
        "cypher_file_ready": bool(job.cypher_commands and Path(job.cypher_commands).exists()),
        "upload_result_available": bool(upload_stats)
    }
```

#### **B. Manual Upload Trigger**
```python
@app.post("/v1/jobs/{job_id}/upload")
async def trigger_manual_upload(
    job_id: str,
    background_tasks: BackgroundTasks,
    upload_options: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Manually trigger Neo4j upload for completed Phase 2 job."""
    
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
    
    # Start upload in background
    background_tasks.add_task(orchestrator._run_uploader, job)
    
    return {
        "job_id": job_id,
        "message": "Upload started",
        "status": "Upload initiated in background"
    }
```

#### **C. Upload Statistics Endpoint**
```python
@app.get("/v1/jobs/{job_id}/neo4j-stats")
async def get_neo4j_stats(job_id: str) -> Dict[str, Any]:
    """Get detailed Neo4j upload statistics."""
    
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
    
    return {
        "job_id": job_id,
        "upload_stats": upload_stats,
        "neo4j_connection": {
            "database": "neo4j",  # From config
            "uri": "bolt://localhost:7687",  # From config
            "status": "connected"
        }
    }
```

### 2. Enhanced Download Endpoints

#### **Update File Downloads**
```python
@app.get("/v1/jobs/{job_id}/files/{file_type}")
async def download_job_file(job_id: str, file_type: str) -> FileResponse:
    """Download job output files including upload results."""
    
    job = orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    file_map = {
        "extraction": job.extraction_output,
        "cypher": job.cypher_commands,
        "tuples": job.tuples_output,
        "upload-result": job.upload_result,  # NEW: Upload result file
        "backup-result": job.backup_result,   # NEW: Backup result file  
        "loader": job.loader_output
    }
    
    file_path = file_map.get(file_type)
    if not file_path:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file_type}. Available: {list(file_map.keys())}"
        )
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found for job {job_id}: {file_type}"
        )
    
    return FileResponse(
        path=file_path,
        filename=Path(file_path).name,
        media_type="application/octet-stream"
    )

@app.get("/v1/backups/{job_id}/download")
async def download_backup_file(job_id: str) -> FileResponse:
    """Download the actual backup tarball file for a job."""
    
    from backend.neo4j_manager.core.database_tracker import DatabaseTracker
    
    tracker = DatabaseTracker()
    backup = await tracker.get_backup_by_job_id(job_id)
    
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
```

---

## UI Integration Strategy

### 1. Frontend Component Architecture

#### **A. Backup Management Component**

```javascript
// BackupManagementPanel.jsx
import React, { useState, useEffect } from 'react';

const BackupManagementPanel = ({ jobId }) => {
    const [backups, setBackups] = useState([]);
    const [currentJobBackup, setCurrentJobBackup] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        loadBackups();
        if (jobId) {
            loadCurrentJobBackup();
        }
    }, [jobId]);
    
    const loadBackups = async () => {
        try {
            const response = await fetch('/v1/backups');
            const data = await response.json();
            setBackups(data.backups);
        } catch (error) {
            console.error('Failed to load backups:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const loadCurrentJobBackup = async () => {
        try {
            const response = await fetch(`/v1/jobs/${jobId}/backup-status`);
            const data = await response.json();
            setCurrentJobBackup(data);
        } catch (error) {
            console.error('Failed to load job backup status:', error);
        }
    };
    
    const restoreBackup = async (backupJobId) => {
        if (!confirm(`Restore database from backup ${backupJobId}? This will replace the current database.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/v1/backups/${backupJobId}/restore`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert('Database restore initiated successfully!');
                loadBackups(); // Refresh backup list
            } else {
                const error = await response.json();
                alert(`Restore failed: ${error.detail}`);
            }
        } catch (error) {
            alert(`Restore failed: ${error.message}`);
        }
    };
    
    const deleteBackup = async (backupJobId) => {
        if (!confirm(`Delete backup ${backupJobId}? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/v1/backups/${backupJobId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                alert('Backup deleted successfully!');
                loadBackups(); // Refresh backup list
            } else {
                const error = await response.json();
                alert(`Delete failed: ${error.detail}`);
            }
        } catch (error) {
            alert(`Delete failed: ${error.message}`);
        }
    };
    
    const downloadBackup = (backupJobId) => {
        const url = `/v1/backups/${backupJobId}/download`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `neo4j_backup_${backupJobId}.tar.gz`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
    
    if (loading) return <div className="loading">Loading backup information...</div>;
    
    return (
        <div className="backup-management-panel">
            <h3>Neo4j Database Backups</h3>
            
            {/* Current Job Backup Status */}
            {jobId && currentJobBackup && (
                <div className="current-job-backup">
                    <h4>Current Job Backup Status</h4>
                    <div className="backup-status">
                        <span className="label">Job ID:</span>
                        <span className="value">{jobId}</span>
                    </div>
                    <div className="backup-status">
                        <span className="label">Backup Created:</span>
                        <span className={`value ${currentJobBackup.backup_completed ? 'success' : 'pending'}`}>
                            {currentJobBackup.backup_completed ? 'Yes' : 'No'}
                        </span>
                    </div>
                    {currentJobBackup.can_restore && (
                        <button 
                            onClick={() => restoreBackup(jobId)}
                            className="btn btn-warning"
                        >
                            Restore This Backup
                        </button>
                    )}
                </div>
            )}
            
            {/* All Available Backups */}
            <div className="all-backups">
                <h4>Available Database Backups ({backups.length})</h4>
                
                {backups.length === 0 ? (
                    <p className="no-backups">No backups available</p>
                ) : (
                    <div className="backup-list">
                        {backups.map(backup => (
                            <div key={backup.job_id} className="backup-item">
                                <div className="backup-info">
                                    <div className="backup-header">
                                        <span className="job-id">Job: {backup.job_id}</span>
                                        <span className="backup-size">{backup.size_mb.toFixed(2)} MB</span>
                                    </div>
                                    <div className="backup-details">
                                        <span className="created-date">
                                            Created: {new Date(backup.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="backup-description">
                                        {backup.description}
                                    </div>
                                </div>
                                
                                <div className="backup-actions">
                                    <button 
                                        onClick={() => downloadBackup(backup.job_id)}
                                        className="btn btn-secondary"
                                        title="Download backup file"
                                    >
                                        Download
                                    </button>
                                    <button 
                                        onClick={() => restoreBackup(backup.job_id)}
                                        className="btn btn-warning"
                                        title="Restore database from this backup"
                                    >
                                        Restore
                                    </button>
                                    <button 
                                        onClick={() => deleteBackup(backup.job_id)}
                                        className="btn btn-danger"
                                        title="Delete this backup"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default BackupManagementPanel;
```

#### **B. Upload Status Component**
```javascript
// UploadStatusPanel.jsx
import React, { useState, useEffect } from 'react';

const UploadStatusPanel = ({ jobId }) => {
    const [uploadStatus, setUploadStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        const checkUploadStatus = async () => {
            try {
                const response = await fetch(`/v1/jobs/${jobId}/upload-status`);
                const status = await response.json();
                setUploadStatus(status);
            } catch (error) {
                console.error('Failed to fetch upload status:', error);
            } finally {
                setLoading(false);
            }
        };
        
        checkUploadStatus();
        
        // Poll for updates if upload is in progress
        if (uploadStatus && !uploadStatus.upload_completed) {
            const interval = setInterval(checkUploadStatus, 2000);
            return () => clearInterval(interval);
        }
    }, [jobId, uploadStatus]);
    
    if (loading) return <div className="loading">Checking upload status...</div>;
    
    return (
        <div className="upload-status-panel">
            <h3>Neo4j Upload Status</h3>
            
            <div className="status-grid">
                <div className="status-item">
                    <span className="label">Phase:</span>
                    <span className={`value phase-${uploadStatus.phase}`}>
                        {uploadStatus.phase}
                    </span>
                </div>
                
                <div className="status-item">
                    <span className="label">Status:</span>
                    <span className={`value status-${uploadStatus.status}`}>
                        {uploadStatus.status}
                    </span>
                </div>
                
                <div className="status-item">
                    <span className="label">Cypher File Ready:</span>
                    <span className={`value ${uploadStatus.cypher_file_ready ? 'ready' : 'pending'}`}>
                        {uploadStatus.cypher_file_ready ? 'Yes' : 'No'}
                    </span>
                </div>
            </div>
            
            {uploadStatus.upload_stats && (
                <UploadStatsDisplay stats={uploadStatus.upload_stats} />
            )}
            
            <div className="actions">
                {uploadStatus.cypher_file_ready && !uploadStatus.upload_completed && (
                    <button 
                        onClick={() => triggerManualUpload(jobId)}
                        className="btn btn-primary"
                    >
                        Start Neo4j Upload
                    </button>
                )}
                
                {uploadStatus.upload_result_available && (
                    <DownloadButton 
                        jobId={jobId}
                        fileType="upload-result"
                        label="Download Upload Results"
                    />
                )}
            </div>
        </div>
    );
};

const UploadStatsDisplay = ({ stats }) => (
    <div className="upload-stats">
        <h4>Upload Statistics</h4>
        <div className="stats-grid">
            <div className="stat-item">
                <span className="stat-label">Nodes Created:</span>
                <span className="stat-value">{stats.nodes_created || 0}</span>
            </div>
            <div className="stat-item">
                <span className="stat-label">Relationships Created:</span>
                <span className="stat-value">{stats.relationships_created || 0}</span>
            </div>
            <div className="stat-item">
                <span className="stat-label">Commands Executed:</span>
                <span className="stat-value">{stats.total_commands_executed || 0}</span>
            </div>
            <div className="stat-item">
                <span className="stat-label">Upload Duration:</span>
                <span className="stat-value">{stats.upload_duration_seconds || 0}s</span>
            </div>
        </div>
    </div>
);

const triggerManualUpload = async (jobId) => {
    try {
        const response = await fetch(`/v1/jobs/${jobId}/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            alert('Upload started successfully!');
        } else {
            const error = await response.json();
            alert(`Upload failed: ${error.detail}`);
        }
    } catch (error) {
        alert(`Upload failed: ${error.message}`);
    }
};

export default UploadStatusPanel;
```

#### **B. Enhanced Analysis Dashboard**
```javascript
// AnalysisDashboard.jsx - Enhanced with Phase 3
import React, { useState, useEffect } from 'react';
import UploadStatusPanel from './UploadStatusPanel';

const AnalysisDashboard = ({ jobId }) => {
    const [jobStatus, setJobStatus] = useState(null);
    const [activeTab, setActiveTab] = useState('progress');
    
    useEffect(() => {
        const pollJobStatus = async () => {
            try {
                const response = await fetch(`/v1/jobs/${jobId}/status`);
                const status = await response.json();
                setJobStatus(status);
                
                // Continue polling if not completed
                if (status.status !== 'completed' && status.status !== 'failed') {
                    setTimeout(pollJobStatus, 2000);
                }
            } catch (error) {
                console.error('Failed to fetch job status:', error);
            }
        };
        
        pollJobStatus();
    }, [jobId]);
    
    return (
        <div className="analysis-dashboard">
            <div className="dashboard-header">
                <h2>Analysis Dashboard</h2>
                <div className="job-info">
                    <span className="job-id">Job ID: {jobId}</span>
                    <span className={`job-status status-${jobStatus?.status}`}>
                        {jobStatus?.status || 'unknown'}
                    </span>
                </div>
            </div>
            
            <div className="progress-indicator">
                <div className="phase-steps">
                    <PhaseStep 
                        phase="extraction" 
                        active={jobStatus?.phase === 'extraction'}
                        completed={['transformation', 'loading', 'completed'].includes(jobStatus?.phase)}
                        label="Phase 1: Code Extraction"
                    />
                    <PhaseStep 
                        phase="transformation" 
                        active={jobStatus?.phase === 'transformation'}
                        completed={['loading', 'completed'].includes(jobStatus?.phase)}
                        label="Phase 2: Neo4j Transformation"
                    />
                    <PhaseStep 
                        phase="loading" 
                        active={jobStatus?.phase === 'loading'}
                        completed={jobStatus?.phase === 'completed'}
                        label="Phase 3: Neo4j Upload"
                    />
                </div>
                
                {jobStatus?.progress && (
                    <div className="progress-bar">
                        <div 
                            className="progress-fill" 
                            style={{ width: `${jobStatus.progress}%` }}
                        />
                        <span className="progress-text">{jobStatus.progress}%</span>
                    </div>
                )}
            </div>
            
            <div className="dashboard-tabs">
                <button 
                    className={`tab ${activeTab === 'progress' ? 'active' : ''}`}
                    onClick={() => setActiveTab('progress')}
                >
                    Progress
                </button>
                <button 
                    className={`tab ${activeTab === 'results' ? 'active' : ''}`}
                    onClick={() => setActiveTab('results')}
                >
                    Results
                </button>
                <button 
                    className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
                    onClick={() => setActiveTab('upload')}
                >
                    Neo4j Upload
                </button>
            </div>
            
            <div className="tab-content">
                {activeTab === 'progress' && (
                    <ProgressPanel jobStatus={jobStatus} />
                )}
                
                {activeTab === 'results' && (
                    <ResultsPanel jobId={jobId} jobStatus={jobStatus} />
                )}
                
                {activeTab === 'upload' && (
                    <UploadStatusPanel jobId={jobId} />
                )}
            </div>
        </div>
    );
};

const PhaseStep = ({ phase, active, completed, label }) => (
    <div className={`phase-step ${active ? 'active' : ''} ${completed ? 'completed' : ''}`}>
        <div className="step-icon">
            {completed ? '✓' : (active ? '⟳' : '○')}
        </div>
        <div className="step-label">{label}</div>
    </div>
);

const ResultsPanel = ({ jobId, jobStatus }) => {
    const [results, setResults] = useState(null);
    
    useEffect(() => {
        if (jobStatus?.status === 'completed') {
            fetchResults();
        }
    }, [jobStatus]);
    
    const fetchResults = async () => {
        try {
            const response = await fetch(`/v1/jobs/${jobId}/results`);
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error('Failed to fetch results:', error);
        }
    };
    
    if (jobStatus?.status !== 'completed') {
        return <div className="results-pending">Analysis not yet completed</div>;
    }
    
    return (
        <div className="results-panel">
            <h3>Analysis Results</h3>
            
            <div className="download-options">
                <h4>Available Downloads</h4>
                
                <div className="download-grid">
                    <DownloadOption
                        jobId={jobId}
                        fileType="extraction"
                        title="Phase 1: Extraction Data"
                        description="Raw extraction data (JSON format)"
                    />
                    
                    <DownloadOption
                        jobId={jobId}
                        fileType="cypher"
                        title="Phase 2: Neo4j Cypher Commands"
                        description="Ready-to-execute Cypher commands"
                    />
                    
                    <DownloadOption
                        jobId={jobId}
                        fileType="tuples"
                        title="Phase 2: JSON Tuples"
                        description="Structured JSON with nodes and relationships"
                    />
                    
                    <DownloadOption
                        jobId={jobId}
                        fileType="upload-result"
                        title="Phase 3: Upload Results"
                        description="Neo4j upload statistics and results"
                    />
                </div>
            </div>
        </div>
    );
};

const DownloadOption = ({ jobId, fileType, title, description }) => (
    <div className="download-option">
        <div className="download-info">
            <h5>{title}</h5>
            <p>{description}</p>
        </div>
        <button 
            onClick={() => downloadFile(jobId, fileType)}
            className="btn btn-secondary"
        >
            Download
        </button>
    </div>
);

const downloadFile = (jobId, fileType) => {
    const url = `/v1/jobs/${jobId}/files/${fileType}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileType}_${jobId}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};

export default AnalysisDashboard;
```

### 2. API Integration Patterns

#### **A. Complete Analysis Workflow**
```javascript
// AnalysisService.js - Complete workflow management
class AnalysisService {
    
    async startFullAnalysis(codebasePath) {
        try {
            // Start Phase 1 & 2
            const startResponse = await fetch('/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    codebase_path: codebasePath,
                    include_neo4j_upload: true  // Request automatic Phase 3
                })
            });
            
            const { job_id } = await startResponse.json();
            
            // Monitor progress through all phases
            return this.monitorAnalysisProgress(job_id);
            
        } catch (error) {
            throw new Error(`Failed to start analysis: ${error.message}`);
        }
    }
    
    async monitorAnalysisProgress(jobId) {
        return new Promise((resolve, reject) => {
            const checkProgress = async () => {
                try {
                    const response = await fetch(`/v1/jobs/${jobId}/status`);
                    const status = await response.json();
                    
                    // Emit progress events
                    this.emit('progress', status);
                    
                    if (status.status === 'completed') {
                        // Get final results
                        const results = await this.getAnalysisResults(jobId);
                        resolve(results);
                    } else if (status.status === 'failed') {
                        reject(new Error(status.error || 'Analysis failed'));
                    } else {
                        // Continue monitoring
                        setTimeout(checkProgress, 2000);
                    }
                    
                } catch (error) {
                    reject(error);
                }
            };
            
            checkProgress();
        });
    }
    
    async getAnalysisResults(jobId) {
        const [results, uploadStatus, neo4jStats] = await Promise.all([
            fetch(`/v1/jobs/${jobId}/results`).then(r => r.json()),
            fetch(`/v1/jobs/${jobId}/upload-status`).then(r => r.json()),
            fetch(`/v1/jobs/${jobId}/neo4j-stats`).then(r => r.json()).catch(() => null)
        ]);
        
        return {
            job_id: jobId,
            analysis_results: results,
            upload_status: uploadStatus,
            neo4j_stats: neo4jStats,
            download_links: {
                extraction: `/v1/jobs/${jobId}/files/extraction`,
                cypher: `/v1/jobs/${jobId}/files/cypher`,
                tuples: `/v1/jobs/${jobId}/files/tuples`,
                upload_result: `/v1/jobs/${jobId}/files/upload-result`
            }
        };
    }
    
    async triggerManualUpload(jobId) {
        const response = await fetch(`/v1/jobs/${jobId}/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        return response.json();
    }
    
    // Event emitter functionality for progress updates
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    constructor() {
        this.listeners = {};
    }
}

export default new AnalysisService();
```

---

## Implementation Roadmap

### Phase 1: Foundation & Neo4j Manager (Week 1-2)

**Priority: HIGH**

1. **Create Neo4j Manager Domain Structure**
   - Set up `/backend/neo4j_manager/` directory structure  
   - Implement backup models (`BackupResult`, `RestoreResult`, `BackupMetadata`)
   - Create CLI entry point (`neo4j_manager/main.py`)

2. **Core Backup Management**
   - Implement `BackupManager` with tarball operations
   - Add `Neo4jService` for service lifecycle management
   - Create `TarballManager` for compression/extraction
   - Implement `DatabaseTracker` for job_id to backup mapping

3. **Create Upload Domain Structure**  
   - Set up `/backend/uploader/` directory structure
   - Implement base models (`UploadResult`, `UploadMetadata`, `BatchResult`)
   - Create CLI entry point (`uploader/main.py`)

4. **Enhanced Neo4j Client**
   - Implement `Neo4jClient` with connection pooling
   - Add health monitoring and retry logic
   - Integrate with existing configuration system

5. **Basic Integration Testing**
   - Test Neo4j backup/restore functionality
   - Test Neo4j connection with existing utilities
   - Validate Phase 2 output compatibility
   - Create integration test suite

### Phase 2: Core Upload Functionality & Integration (Week 3-4)

**Priority: HIGH**

1. **Batch Upload System**
   - Implement `BatchUploader` with streaming support
   - Add memory-efficient file processing
   - Implement progress tracking system

2. **Backup-Upload Integration**
   - Integrate backup creation with upload workflow
   - Implement pre-upload backup automation
   - Add backup failure recovery mechanisms
   - Create database clearing functionality

3. **Orchestrator Integration** 
   - Update orchestrator to include Phase 3a (backup) and 3b (upload)
   - Add Neo4j Manager CLI execution logic
   - Add Upload CLI execution logic  
   - Update job tracking for backup and upload files
   - Implement backup-upload-restore error recovery

4. **Validation Services**
   - Implement Cypher file validation
   - Add pre-upload checks and health validation
   - Add backup integrity validation
   - Error handling and recovery mechanisms

### Phase 3: API & UI Integration (Week 5-6)

**Priority: MEDIUM**

1. **API Endpoints**
   - Add backup management endpoints (`/v1/backups`, `/v1/jobs/{id}/backup-status`)
   - Add upload status endpoints  
   - Implement manual upload triggers
   - Implement backup restore and delete endpoints
   - Enhance download endpoints for upload results and backup files

2. **Frontend Components**
   - Create `BackupManagementPanel` component with restore/delete functionality
   - Create `UploadStatusPanel` component
   - Update analysis dashboard with backup and upload support
   - Implement progress visualization for backup and upload phases
   - Add backup browsing and management interface

3. **Complete Workflow Testing**
   - End-to-end pipeline testing (backup → clear → upload)
   - UI integration testing for backup management
   - Backup/restore functionality testing
   - Performance optimization

### Phase 4: Production Readiness (Week 7-8)

**Priority: MEDIUM**

1. **Performance Optimization**
   - Memory usage optimization
   - Batch size tuning
   - Connection pool optimization

2. **Error Handling & Recovery**
   - Comprehensive error scenarios
   - Upload resume functionality
   - Transaction rollback mechanisms

3. **Documentation & Deployment**
   - API documentation updates
   - Deployment configuration
   - Monitoring and logging enhancements

---

## Error Handling & Recovery

### 1. Connection Errors

**Scenario:** Neo4j database unavailable or connection timeout

**Strategy:**
- Automatic retry with exponential backoff
- Connection health monitoring
- Graceful degradation with detailed error reporting

**Implementation:**
```python
class ConnectionRetryStrategy:
    async def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await operation()
            except ServiceUnavailable as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Neo4j unavailable after {max_retries} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Partial Upload Failures

**Scenario:** Some batches succeed, others fail during large upload

**Strategy:**
- Transaction-based batch processing
- Resume capability from last successful batch
- Detailed failure reporting with recovery options

**Implementation:**
```python
class ResumableUpload:
    async def resume_upload(self, job_id: str, last_successful_batch: int):
        # Load remaining commands from last successful point
        # Continue upload from where it left off
        # Update progress accordingly
```

### 3. Data Validation Errors

**Scenario:** Invalid Cypher commands or malformed data

**Strategy:**
- Pre-upload validation of all commands
- Detailed error reporting with line numbers
- Option to skip invalid commands and continue

**Implementation:**
```python
class ValidationService:
    async def validate_cypher_file(self, file_path: str) -> ValidationResult:
        # Parse and validate each Cypher command
        # Report syntax errors with line numbers
        # Provide suggestions for common issues
```

---

## Testing Strategy

### 1. Unit Testing

**Components to Test:**
- Neo4j client connection and query execution
- Batch uploader with mock data
- Validation service with invalid inputs
- Progress tracking and reporting

**Test Framework:** `pytest` with `pytest-asyncio`

**Example Test:**
```python
@pytest.mark.asyncio
async def test_neo4j_client_batch_upload():
    client = Neo4jClient(uri="bolt://localhost:7687")
    
    test_commands = [
        "CREATE (n:TestNode {name: 'test1'})",
        "CREATE (n:TestNode {name: 'test2'})"
    ]
    
    result = await client.execute_cypher_batch(test_commands)
    
    assert result.success
    assert result.nodes_created == 2
    assert len(result.errors) == 0
```

### 2. Integration Testing

**Pipeline Testing:**
- Complete Phase 1 → Phase 2 → Phase 3 flow
- File path consistency across phases
- Job ID tracking through all phases

**Database Testing:**
- Neo4j container setup for CI/CD
- Schema validation after upload
- Data integrity checks

### 3. Performance Testing

**Load Testing:**
- Large file uploads (>10MB Cypher files)
- High batch volume processing
- Memory usage monitoring

**Benchmarking:**
- Upload speed vs batch size optimization
- Connection pool sizing
- Memory efficiency measurements

---

## Performance Considerations

### 1. Memory Management

**Challenge:** Large Cypher files may consume excessive memory

**Solution:**
- Streaming file processing
- Configurable memory limits
- Batch size optimization based on available memory

**Implementation:**
```python
class MemoryAwareUploader:
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.current_memory_usage = 0
    
    async def process_batch(self, batch):
        # Monitor memory usage
        # Adjust batch size dynamically if needed
```

### 2. Connection Optimization  

**Configuration Recommendations:**
- Connection pool size: 20-50 connections
- Connection lifetime: 1 hour
- Batch size: 100-500 commands (depending on complexity)
- Timeout: 60 seconds per batch

### 3. Database Performance

**Neo4j Optimization:**
- Index creation for frequently queried properties
- Periodic compaction of transaction logs
- Memory allocation tuning (dbms.memory.heap.max_size)

---

## Security & Configuration

### 1. Authentication & Authorization

**Neo4j Security:**
- Encrypted connections (bolt+s://)
- Role-based access control
- Credential management via environment variables

**Configuration:**
```python
# Environment variables for production
NEO4J_URI=bolt+s://production-neo4j:7687
NEO4J_USER=upload_service
NEO4J_PASSWORD=<secure-password>
NEO4J_DATABASE=production_graph
```

### 2. Input Validation

**Security Measures:**
- Parameterized Cypher queries (prevent injection)
- File size limits for uploads
- Content validation before execution

**Example:**
```python
def validate_cypher_command(command: str) -> bool:
    # Check for dangerous operations
    dangerous_patterns = ['DROP', 'DELETE', 'DETACH DELETE']
    command_upper = command.upper()
    
    for pattern in dangerous_patterns:
        if pattern in command_upper:
            return False
    
    return True
```

### 3. Monitoring & Logging

**Observability:**
- Structured logging with job_id correlation
- Performance metrics collection for backup and upload operations
- Error rate monitoring for backup/restore failures
- Connection health dashboards
- Backup storage monitoring and cleanup alerts

**Integration with existing logging:**
```python
# Upload logging
logger.info(
    "Upload completed",
    extra={
        "job_id": job_id,
        "nodes_created": result.nodes_created,
        "relationships_created": result.relationships_created,
        "duration_seconds": result.upload_duration_seconds
    }
)

# Backup logging
logger.info(
    "Backup completed",
    extra={
        "job_id": job_id,
        "backup_path": result.backup_path,
        "backup_size_mb": result.backup_size_bytes / 1024 / 1024,
        "backup_duration_seconds": result.backup_duration_seconds
    }
)
```

### 4. Backup Storage Management

**Storage Configuration:**
- Configurable backup location (default: `./neo4j_backups`)
- Automatic cleanup of old backups (configurable retention policy)
- Backup compression using gzip for space efficiency
- Job ID to backup path mapping in SQLite database

**Configuration:**
```python
# Additional config.py settings for backup management
class DatabaseSettings(BaseSettings):
    # ... existing Neo4j settings ...
    
    # Backup management
    neo4j_data_dir: str = Field(default="/var/lib/neo4j/data", description="Neo4j data directory")
    backup_storage_dir: str = Field(default="./neo4j_backups", description="Backup storage directory")
    backup_compression: str = Field(default="gzip", description="Backup compression method")
    backup_retention_days: int = Field(default=30, description="Backup retention period in days")
    max_backup_storage_gb: int = Field(default=50, description="Maximum backup storage in GB")
```

---

## Conclusion

This comprehensive Phase 3 development plan with **Neo4j Manager** integration addresses the critical single-database constraint while leveraging the robust Neo4j infrastructure already present in the backend. The enhanced plan provides:

### **Key Architectural Innovations:**

1. **Neo4j Manager Domain** - New backup and versioning system that:
   - Automatically creates job_id-based database backups before each upload
   - Manages tarball creation and storage outside Neo4j data directory  
   - Provides complete database restore capabilities
   - Tracks all database versions with job_id mapping

2. **Enhanced Phase 3 Workflow:**
   ```
   Phase 3a: Backup Current Database → neo4j_backup_{job_id}_{timestamp}.tar.gz
   Phase 3b: Clear Database → Empty Neo4j instance
   Phase 3c: Upload New Data → Populated Neo4j with new analysis
   ```

### **Key Strengths:**

1. **Solves Single-Database Constraint** - Elegant backup/restore solution enables database versioning while maintaining single Neo4j instance

2. **Built on Solid Foundation** - Utilizes existing Neo4j utilities, configuration management, and established architectural patterns

3. **Production Ready** - Comprehensive error handling, retry logic, progress tracking, backup integrity verification, and performance optimization

4. **Database Version Management** - Complete backup lifecycle with restore capabilities, cleanup policies, and UI management interface

5. **Seamless Integration** - Maintains CLI consistency, job tracking, and file naming conventions from previous phases  

6. **User-Friendly UI** - Complete frontend integration with real-time progress, backup management, restore capabilities, and comprehensive downloads

7. **Scalable Architecture** - Memory-efficient streaming, configurable batch processing, connection pooling, and backup storage management

### **Implementation Timeline:** 8 weeks total

- **Weeks 1-2:** Neo4j Manager foundation, backup/restore system, and core upload infrastructure
- **Weeks 3-4:** Backup-upload integration, orchestrator updates, and workflow automation
- **Weeks 5-6:** Backup management APIs, UI components, and complete workflow testing
- **Weeks 7-8:** Production hardening, performance optimization, and backup storage management

### **Expected Outcomes:**

- **Complete 4-Phase Workflow:** Raw Code → JSON → Neo4j Tuples → Backup → Graph Database
- **Database Version Management:** Automatic backup creation, job_id-based restoration, backup browsing/management
- **Full UI Integration:** Real-time progress, backup management interface, manual triggers, comprehensive downloads
- **Production Reliability:** Backup/restore error recovery, health monitoring, performance optimization, storage management
- **Developer Experience:** Consistent APIs, comprehensive logging, easy debugging, database versioning

### **Critical Benefits for Single-Database Constraint:**

1. **Zero Data Loss Risk** - Every upload automatically preserves previous database state
2. **Instant Rollback Capability** - Failed uploads can immediately restore previous state  
3. **Historical Analysis Access** - Users can restore any previous analysis for comparison
4. **Safe Experimentation** - Developers can safely test uploads knowing rollback is available
5. **Audit Trail** - Complete history of database changes with job_id correlation

This enhanced plan positions Phase 3 as a robust, production-ready component that not only completes the Python Debug Tool's transformation from raw code analysis to fully-populated Neo4j graph database, but also provides enterprise-grade database version management that elegantly solves the single-database constraint while enabling powerful backup and restore capabilities.