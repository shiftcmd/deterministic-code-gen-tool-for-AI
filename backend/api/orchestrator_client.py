"""
Orchestrator Client for Main API Integration

Provides HTTP client functionality to communicate with the orchestrator service
running on a separate port, enabling the main API to proxy requests to the
actual analysis pipeline.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """HTTP client for communicating with the orchestrator service."""
    
    def __init__(self, base_url: str = "http://localhost:8078"):
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(60.0)  # 60 second timeout for analysis requests
        
    async def health_check(self) -> bool:
        """Check if orchestrator service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Orchestrator health check failed: {e}")
            return False
    
    async def start_analysis(self, codebase_path: str, **kwargs) -> Dict[str, Any]:
        """Start analysis pipeline via orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "codebase_path": codebase_path,
                    **kwargs
                }
                
                logger.info(f"Starting analysis via orchestrator: {payload}")
                response = await client.post(
                    f"{self.base_url}/v1/analyze",
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"Orchestrator returned status {response.status_code}: {response.text}")
                
                result = response.json()
                logger.info(f"Analysis started successfully: {result}")
                return result
                
        except httpx.TimeoutException:
            raise Exception("Orchestrator request timed out")
        except Exception as e:
            logger.error(f"Failed to start analysis via orchestrator: {e}")
            raise Exception(f"Orchestrator communication failed: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status from orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/v1/jobs/{job_id}/status")
                
                if response.status_code == 404:
                    raise Exception(f"Job not found: {job_id}")
                elif response.status_code != 200:
                    raise Exception(f"Orchestrator returned status {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get job status from orchestrator: {e}")
            raise
    
    async def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get job results from orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/v1/jobs/{job_id}/results")
                
                if response.status_code == 404:
                    raise Exception(f"Job not found: {job_id}")
                elif response.status_code != 200:
                    raise Exception(f"Orchestrator returned status {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get job results from orchestrator: {e}")
            raise
    
    async def stop_job(self, job_id: str) -> Dict[str, Any]:
        """Stop a running job via orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/v1/jobs/{job_id}/stop")
                
                if response.status_code == 404:
                    raise Exception(f"Job not found: {job_id}")
                elif response.status_code != 200:
                    raise Exception(f"Orchestrator returned status {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to stop job via orchestrator: {e}")
            raise
    
    async def download_job_file(self, job_id: str, file_type: str) -> bytes:
        """Download a job file from orchestrator."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/v1/jobs/{job_id}/files/{file_type}")
                
                if response.status_code == 404:
                    raise Exception(f"File not found: {file_type} for job {job_id}")
                elif response.status_code != 200:
                    raise Exception(f"Orchestrator returned status {response.status_code}")
                
                return response.content
                
        except Exception as e:
            logger.error(f"Failed to download job file from orchestrator: {e}")
            raise


# Global orchestrator client instance
orchestrator_client = OrchestratorClient()


def map_orchestrator_status_to_frontend(orchestrator_status: Dict[str, Any]) -> Dict[str, Any]:
    """Map orchestrator status response to frontend expected format."""
    
    # Map status values
    status_mapping = {
        "pending": "queued",
        "extracting": "running",
        "transforming": "running", 
        "loading": "running",
        "completed": "completed",
        "failed": "failed"
    }
    
    mapped_status = status_mapping.get(orchestrator_status.get("status", "unknown"), "unknown")
    
    # Calculate progress based on phase
    progress_mapping = {
        "pending": 0,
        "extracting": 25,
        "transforming": 50,
        "loading": 75,
        "completed": 100,
        "failed": 0
    }
    
    progress = progress_mapping.get(orchestrator_status.get("status", "pending"), 0)
    
    # Map phases for frontend timeline
    phases = []
    current_phase = orchestrator_status.get("phase", "initialization")
    
    phase_sequence = [
        ("initialization", "Initialization"),
        ("extracting", "Code Parsing"), 
        ("transforming", "Graph Building"),
        ("loading", "Neo4j Upload")
    ]
    
    for phase_key, phase_title in phase_sequence:
        is_active = (current_phase == phase_key and mapped_status == "running")
        is_completed = (phase_sequence.index((phase_key, phase_title)) < 
                       phase_sequence.index((current_phase, current_phase.title())) or
                       mapped_status == "completed")
        
        phases.append({
            "name": phase_key,
            "title": phase_title,
            "active": is_active,
            "completed": is_completed
        })
    
    return {
        "run_id": orchestrator_status.get("job_id", "unknown"),
        "job_id": orchestrator_status.get("job_id", "unknown"),
        "status": mapped_status,
        "progress": progress,
        "message": orchestrator_status.get("message", "Processing..."),
        "phase": current_phase,
        "started_at": orchestrator_status.get("started_at", ""),
        "updated_at": orchestrator_status.get("updated_at", ""),
        "completed_at": orchestrator_status.get("completed_at"),
        "error": orchestrator_status.get("error"),
        "phases": phases,
        "metadata": orchestrator_status.get("metadata", {}),
        "files_processed": orchestrator_status.get("metadata", {}).get("files_processed", 0),
        "total_files": orchestrator_status.get("metadata", {}).get("total_files", 0)
    }


def map_frontend_request_to_orchestrator(frontend_request: Dict[str, Any]) -> Dict[str, Any]:
    """Map frontend analysis request to orchestrator format."""
    
    return {
        "codebase_path": frontend_request.get("path", "."),
        "neo4j_uri": frontend_request.get("neo4j_uri"),
        "neo4j_user": frontend_request.get("neo4j_user"), 
        "neo4j_password": frontend_request.get("neo4j_password")
    }