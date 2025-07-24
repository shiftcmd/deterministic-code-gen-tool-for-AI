"""
File system and project file routes for the Python Debug Tool API.
Clean API layer - no business logic, only HTTP handling.
"""

import sys
import os
import fastapi
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import service layer (not domain logic)
from parser.dev.services.file_service import FileSystemService

router = APIRouter(prefix="/api", tags=["files"])

# Initialize service
file_service = FileSystemService()


class FileInfo(BaseModel):
    """File information model."""
    name: str
    path: str
    type: str
    size: int
    is_python: bool = False
    last_modified: Optional[float] = None


class DirectoryRequest(BaseModel):
    """Directory scanning request model."""
    path: str
    include_hidden: bool = False
    python_only: bool = False


@router.get("/files")
async def get_project_files(
    path: str = Query(default=".", description="Directory path to scan"),
    python_only: bool = Query(default=True, description="Only return Python files"),
    limit: int = Query(default=100, description="Maximum number of files to return")
) -> Dict[str, Any]:
    """Get project files from the specified directory."""
    
    try:
        # Delegate to service layer
        result = await file_service.get_project_files(
            path=path,
            python_only=python_only,
            limit=limit
        )
        return result
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning directory: {str(e)}")


@router.get("/filesystem/browse")
async def browse_filesystem(
    path: str = Query(default=".", description="Directory path to browse"),
    show_hidden: bool = Query(default=False, description="Show hidden files and directories")
) -> Dict[str, Any]:
    """Browse filesystem structure with directories and files."""
    
    try:
        # Delegate to service layer
        result = await file_service.browse_filesystem(
            path=path,
            include_hidden=show_hidden
        )
        return result
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied accessing: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error browsing filesystem: {str(e)}")


@router.post("/filesystem/validate")
async def validate_filesystem_path(request: DirectoryRequest) -> Dict[str, Any]:
    """Validate if a filesystem path exists and is accessible."""
    
    try:
        # Delegate to service layer
        result = await file_service.validate_path(
            path=request.path,
            include_hidden=request.include_hidden,
            python_only=request.python_only
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating path: {str(e)}") 