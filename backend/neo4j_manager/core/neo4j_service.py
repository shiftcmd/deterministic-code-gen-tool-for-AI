"""
Neo4j Service Manager - Controls Neo4j service lifecycle

Handles starting, stopping, and health checking of Neo4j service.
"""

import asyncio
import logging
import subprocess
import time
from typing import Optional, List
from datetime import datetime

from ..models.backup_metadata import ServiceOperationResult

logger = logging.getLogger(__name__)


class Neo4jService:
    """Manages Neo4j service lifecycle operations."""
    
    def __init__(self, service_name: str = "neo4j"):
        self.service_name = service_name
        self.systemctl_available = self._check_systemctl()
        self.docker_available = self._check_docker()
    
    def _check_systemctl(self) -> bool:
        """Check if systemctl is available."""
        try:
            subprocess.run(["which", "systemctl"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_docker(self) -> bool:
        """Check if docker is available."""
        try:
            subprocess.run(["which", "docker"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def stop(self, timeout_seconds: int = 60) -> ServiceOperationResult:
        """
        Stop the Neo4j service.
        
        Args:
            timeout_seconds: Maximum time to wait for service to stop
        
        Returns:
            ServiceOperationResult with status
        """
        result = ServiceOperationResult(operation="stop")
        start_time = datetime.now()
        
        try:
            logger.info("Stopping Neo4j service...")
            
            # Try systemctl first
            if self.systemctl_available:
                stop_result = await self._stop_systemctl()
                if stop_result:
                    result.success = True
                    result.duration_seconds = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Neo4j stopped via systemctl in {result.duration_seconds:.2f}s")
                    return result
            
            # Try docker if systemctl failed or unavailable
            if self.docker_available:
                stop_result = await self._stop_docker()
                if stop_result:
                    result.success = True
                    result.duration_seconds = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Neo4j stopped via docker in {result.duration_seconds:.2f}s")
                    return result
            
            # Try direct process kill as last resort
            stop_result = await self._stop_process()
            if stop_result:
                result.success = True
                result.duration_seconds = (datetime.now() - start_time).total_seconds()
                logger.info(f"Neo4j stopped via process kill in {result.duration_seconds:.2f}s")
                return result
            
            result.error = "Failed to stop Neo4j - no suitable method available"
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop Neo4j: {e}")
            result.error = str(e)
            return result
    
    async def start(self, timeout_seconds: int = 60) -> ServiceOperationResult:
        """
        Start the Neo4j service.
        
        Args:
            timeout_seconds: Maximum time to wait for service to start
        
        Returns:
            ServiceOperationResult with status
        """
        result = ServiceOperationResult(operation="start")
        start_time = datetime.now()
        
        try:
            logger.info("Starting Neo4j service...")
            
            # Try systemctl first
            if self.systemctl_available:
                start_result = await self._start_systemctl()
                if start_result:
                    result.success = True
                    result.duration_seconds = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Neo4j started via systemctl in {result.duration_seconds:.2f}s")
                    return result
            
            # Try docker if systemctl failed or unavailable
            if self.docker_available:
                start_result = await self._start_docker()
                if start_result:
                    result.success = True
                    result.duration_seconds = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Neo4j started via docker in {result.duration_seconds:.2f}s")
                    return result
            
            result.error = "Failed to start Neo4j - no suitable method available"
            return result
            
        except Exception as e:
            logger.error(f"Failed to start Neo4j: {e}")
            result.error = str(e)
            return result
    
    async def restart(self, timeout_seconds: int = 120) -> ServiceOperationResult:
        """
        Restart the Neo4j service.
        
        Args:
            timeout_seconds: Maximum time to wait for service to restart
        
        Returns:
            ServiceOperationResult with status
        """
        result = ServiceOperationResult(operation="restart")
        start_time = datetime.now()
        
        try:
            # Stop service
            stop_result = await self.stop(timeout_seconds // 2)
            if not stop_result.success:
                result.error = f"Failed to stop service: {stop_result.error}"
                return result
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Start service
            start_result = await self.start(timeout_seconds // 2)
            if not start_result.success:
                result.error = f"Failed to start service: {start_result.error}"
                return result
            
            result.success = True
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            logger.info(f"Neo4j restarted in {result.duration_seconds:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to restart Neo4j: {e}")
            result.error = str(e)
            return result
    
    async def wait_for_ready(self, timeout_seconds: int = 60) -> ServiceOperationResult:
        """
        Wait for Neo4j to be ready to accept connections.
        
        Args:
            timeout_seconds: Maximum time to wait
        
        Returns:
            ServiceOperationResult with readiness status
        """
        result = ServiceOperationResult(operation="wait_for_ready")
        start_time = datetime.now()
        
        try:
            logger.info("Waiting for Neo4j to be ready...")
            
            # Try connecting to Neo4j bolt port (7687) as readiness check
            end_time = time.time() + timeout_seconds
            while time.time() < end_time:
                if await self._check_bolt_port():
                    result.success = True
                    result.duration_seconds = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Neo4j ready in {result.duration_seconds:.2f}s")
                    return result
                
                await asyncio.sleep(1)
            
            result.error = f"Neo4j not ready after {timeout_seconds} seconds"
            return result
            
        except Exception as e:
            logger.error(f"Error waiting for Neo4j: {e}")
            result.error = str(e)
            return result
    
    async def _stop_systemctl(self) -> bool:
        """Stop Neo4j using systemctl."""
        try:
            process = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "stop", self.service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _start_systemctl(self) -> bool:
        """Start Neo4j using systemctl."""
        try:
            process = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "start", self.service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _stop_docker(self) -> bool:
        """Stop Neo4j docker container."""
        try:
            # First try to stop by name
            process = await asyncio.create_subprocess_exec(
                "docker", "stop", "neo4j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _start_docker(self) -> bool:
        """Start Neo4j docker container."""
        try:
            # First try to start existing container
            process = await asyncio.create_subprocess_exec(
                "docker", "start", "neo4j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return True
            
            # If that fails, try to run new container
            process = await asyncio.create_subprocess_exec(
                "docker", "run", "-d",
                "--name", "neo4j",
                "-p", "7474:7474",
                "-p", "7687:7687",
                "-e", "NEO4J_AUTH=neo4j/password",
                "neo4j:latest",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _stop_process(self) -> bool:
        """Stop Neo4j by killing the process."""
        try:
            # Find neo4j process
            process = await asyncio.create_subprocess_exec(
                "pkill", "-f", "neo4j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return True  # pkill returns 0 if processes were found and killed
        except Exception:
            return False
    
    async def _check_bolt_port(self) -> bool:
        """Check if Neo4j bolt port is accessible."""
        try:
            # Try to connect to bolt port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', 7687),
                timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    def get_status(self) -> str:
        """Get current Neo4j service status."""
        try:
            if self.systemctl_available:
                result = subprocess.run(
                    ["systemctl", "is-active", self.service_name],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip()
            
            if self.docker_available:
                result = subprocess.run(
                    ["docker", "ps", "-f", "name=neo4j", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    return "active"
                return "inactive"
            
            return "unknown"
        except Exception:
            return "error"