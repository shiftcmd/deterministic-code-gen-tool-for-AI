"""
Batch Uploader for Neo4j - Optimized bulk upload operations

Handles large-scale uploads with:
- Memory-efficient streaming processing
- Progress tracking and reporting
- Error recovery and partial upload support
"""

import asyncio
import logging
from typing import List, Optional, AsyncIterator
from pathlib import Path
from datetime import datetime

from .neo4j_client import Neo4jClient
from ..services.validation_service import ValidationService
from ..models.upload_result import UploadResult, BatchResult

logger = logging.getLogger(__name__)


class BatchUploader:
    """Optimized batch uploader for Neo4j operations."""
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        batch_size: int = 100,
        max_memory_mb: int = 500
    ):
        self.neo4j_client = neo4j_client
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        
        # Services
        self.validator = ValidationService()
    
    async def upload_from_file(
        self, 
        cypher_file_path: str, 
        job_id: str,
        validate_before_upload: bool = True
    ) -> UploadResult:
        """Upload Cypher commands from file with validation and progress tracking."""
        
        result = UploadResult(job_id=job_id)
        result.cypher_file_path = cypher_file_path
        result.started_at = datetime.now()
        
        try:
            cypher_path = Path(cypher_file_path)
            if not cypher_path.exists():
                result.add_error(f"Cypher file not found: {cypher_file_path}")
                return result
            
            result.cypher_file_size_bytes = cypher_path.stat().st_size
            
            # Validate file before upload
            if validate_before_upload:
                validation_result = await self.validator.validate_cypher_file(cypher_file_path)
                if not validation_result.is_valid:
                    result.add_error(f"Validation failed: {', '.join(validation_result.errors)}")
                    return result
                
                result.total_commands = validation_result.total_commands
                result.estimated_nodes = validation_result.estimated_nodes
                result.estimated_relationships = validation_result.estimated_relationships
            
            # Stream and upload in batches
            async for batch_result in self._stream_upload_batches(cypher_file_path, job_id):
                result.merge_batch_result(batch_result)
            
            result.completed_at = datetime.now()
            if result.completed_at and result.started_at:
                result.upload_duration_seconds = (result.completed_at - result.started_at).total_seconds()
            
            # Mark as successful if no errors
            if not result.has_errors:
                result.success = True
            
            return result
            
        except Exception as e:
            logger.error(f"Upload from file failed: {e}")
            result.add_error(str(e))
            result.completed_at = datetime.now()
            return result
    
    async def upload_from_commands(
        self,
        cypher_commands: List[str],
        job_id: str
    ) -> UploadResult:
        """Upload Cypher commands directly from list."""
        
        result = UploadResult(job_id=job_id)
        result.total_commands = len(cypher_commands)
        result.started_at = datetime.now()
        
        try:
            # Process in batches
            for i in range(0, len(cypher_commands), self.batch_size):
                batch = cypher_commands[i:i + self.batch_size]
                
                batch_result = await self.neo4j_client.execute_cypher_batch(
                    batch, 
                    batch_size=self.batch_size,
                    job_id=job_id
                )
                
                result.merge_stats(batch_result)
            
            result.completed_at = datetime.now()
            if result.completed_at and result.started_at:
                result.upload_duration_seconds = (result.completed_at - result.started_at).total_seconds()
            
            # Mark as successful if no errors
            if not result.has_errors:
                result.success = True
            
            return result
            
        except Exception as e:
            logger.error(f"Upload from commands failed: {e}")
            result.add_error(str(e))
            result.completed_at = datetime.now()
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