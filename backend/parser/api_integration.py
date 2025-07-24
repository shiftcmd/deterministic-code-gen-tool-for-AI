#!/usr/bin/env python3
"""
API Integration for Parser Orchestrator.

This module provides functions that the main FastAPI application
can call to start the parser orchestrator pipeline.
"""

import asyncio
import httpx
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ParserOrchestratorClient:
    """Client for communicating with the parser orchestrator service."""
    
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        """
        Initialize the orchestrator client.
        
        Args:
            orchestrator_url: Base URL of the orchestrator service
        """
        self.orchestrator_url = orchestrator_url
        
    async def start_analysis(
        self,
        codebase_path: str,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new code analysis job.
        
        Args:
            codebase_path: Path to the codebase to analyze
            neo4j_uri: Optional Neo4j connection URI
            neo4j_user: Optional Neo4j username
            neo4j_password: Optional Neo4j password
            
        Returns:
            Dictionary with job_id and status
        """
        request_data = {
            "codebase_path": codebase_path,
            "neo4j_uri": neo4j_uri,
            "neo4j_user": neo4j_user,
            "neo4j_password": neo4j_password
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/v1/analyze",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Started analysis job: {result.get('job_id')}")
                return result
                
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to orchestrator: {e}")
            raise ConnectionError(f"Orchestrator service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Orchestrator returned error: {e.response.status_code}")
            raise ValueError(f"Analysis request failed: {e.response.text}")
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of an analysis job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary with job status information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.orchestrator_url}/v1/jobs/{job_id}/status",
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to get job status: {e}")
            raise ConnectionError(f"Orchestrator service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Job not found: {job_id}")
            logger.error(f"Failed to get job status: {e.response.status_code}")
            raise ValueError(f"Status request failed: {e.response.text}")
    
    async def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get the results of a completed analysis job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary with job results
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.orchestrator_url}/v1/jobs/{job_id}/results",
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"Failed to get job results: {e}")
            raise ConnectionError(f"Orchestrator service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Job not found: {job_id}")
            elif e.response.status_code == 400:
                raise ValueError("Job is still running")
            logger.error(f"Failed to get job results: {e.response.status_code}")
            raise ValueError(f"Results request failed: {e.response.text}")
    
    async def download_job_file(self, job_id: str, file_type: str) -> bytes:
        """
        Download a specific output file from a job.
        
        Args:
            job_id: Job identifier
            file_type: Type of file ('extraction', 'cypher', 'loader')
            
        Returns:
            File content as bytes
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.orchestrator_url}/v1/jobs/{job_id}/files/{file_type}",
                    timeout=30.0
                )
                response.raise_for_status()
                return response.content
                
        except httpx.RequestError as e:
            logger.error(f"Failed to download job file: {e}")
            raise ConnectionError(f"Orchestrator service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"File not found: {job_id}/{file_type}")
            logger.error(f"Failed to download file: {e.response.status_code}")
            raise ValueError(f"File download failed: {e.response.text}")


# Convenience functions for direct use
async def start_parser_analysis(
    codebase_path: str,
    orchestrator_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """
    Convenience function to start parser analysis.
    
    Args:
        codebase_path: Path to the codebase to analyze
        orchestrator_url: Orchestrator service URL
        
    Returns:
        Dictionary with job_id and status
    """
    client = ParserOrchestratorClient(orchestrator_url)
    return await client.start_analysis(codebase_path)


async def get_parser_job_status(
    job_id: str,
    orchestrator_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """
    Convenience function to get parser job status.
    
    Args:
        job_id: Job identifier
        orchestrator_url: Orchestrator service URL
        
    Returns:
        Dictionary with job status
    """
    client = ParserOrchestratorClient(orchestrator_url)
    return await client.get_job_status(job_id)


# Health check function
async def check_orchestrator_health(
    orchestrator_url: str = "http://localhost:8000"
) -> bool:
    """
    Check if the orchestrator service is available.
    
    Args:
        orchestrator_url: Orchestrator service URL
        
    Returns:
        True if service is available, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{orchestrator_url}/docs",  # FastAPI docs endpoint
                timeout=5.0
            )
            return response.status_code == 200
    except Exception:
        return False


# Example usage for testing
async def test_integration():
    """Test the API integration."""
    print("Testing Parser Orchestrator API Integration")
    print("=" * 50)
    
    # Check health
    is_healthy = await check_orchestrator_health()
    print(f"Orchestrator Health: {'✅ Online' if is_healthy else '❌ Offline'}")
    
    if not is_healthy:
        print("⚠️  Start the orchestrator service first:")
        print("   cd /backend/parser/prod/orchestrator")
        print("   python main.py")
        return
    
    # Test analysis start
    try:
        codebase_path = str(Path(__file__).parent.parent)  # Use backend directory
        result = await start_parser_analysis(codebase_path)
        print(f"✅ Analysis started: {result['job_id']}")
        
        # Check status
        job_id = result["job_id"]
        status = await get_parser_job_status(job_id)
        print(f"✅ Job status: {status['status']} - {status['message']}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_integration())