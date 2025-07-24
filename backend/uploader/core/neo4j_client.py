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

try:
    from neo4j import GraphDatabase, AsyncGraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available - install with: pip install neo4j")

from ..models.upload_result import UploadResult, ConnectionHealth

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Enhanced Neo4j client for Phase 3 upload operations."""
    
    def __init__(
        self, 
        uri: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 100
    ):
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available. Install with: pip install neo4j")
        
        # Initialize from config if not provided
        if not uri or not auth:
            from config import get_settings
            settings = get_settings()
            neo4j_config = settings.get_neo4j_config()
            
            self.uri = uri or neo4j_config["uri"]
            self.auth = auth or neo4j_config["auth"]
            self.database = database or neo4j_config["database"]
        else:
            self.uri = uri
            self.auth = auth
            self.database = database
        
        # Connection configuration
        self.driver = None
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        
        # Health monitoring
        self.last_health_check = None
        self.health_check_interval = timedelta(minutes=5)
        
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
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=self.auth
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
                response_time_ms=0,
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
                
                # Report progress
                progress = (processed / total_commands) * 100
                logger.info(f"Upload progress: {progress:.1f}% ({processed}/{total_commands})")
            
            # Update final statistics
            end_time = datetime.now()
            upload_duration = (end_time - start_time).total_seconds()
            
            result.upload_duration_seconds = upload_duration
            result.total_commands_executed = processed
            result.started_at = start_time
            result.completed_at = end_time
            
            self.connection_stats["successful_queries"] += processed
            self.connection_stats["total_upload_time"] += upload_duration
            self.connection_stats["last_upload"] = end_time
            
            if not result.has_errors:
                result.success = True
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
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
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
                                batch_result.add_error(f"Command failed: {str(e)}", command)
                
                return batch_result
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    delay = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
                    logger.warning(f"Batch failed, retrying in {delay}s (attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Batch failed after {max_retries} retries: {e}")
                    batch_result = UploadResult(job_id=job_id)
                    batch_result.add_error(f"Batch failed after retries: {str(e)}")
                    return batch_result
    
    async def _verify_connectivity(self) -> None:
        """Verify database connectivity with detailed error reporting."""
        try:
            async with self.driver.session() as session:
                await session.run("RETURN 1")
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