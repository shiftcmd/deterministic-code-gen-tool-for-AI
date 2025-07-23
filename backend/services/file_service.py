"""
File System Service Layer

Handles file system operations and business logic.
Keeps domain logic separate from API layer.
"""

import os
from pathlib import Path
from typing import Dict, Any


class FileSystemService:
    """
    Service layer for file system operations.
    
    Handles business logic for file operations without HTTP concerns.
    """
    
    def __init__(self):
        self.max_file_size = 1024 * 1024  # 1MB default limit
        # Get the actual project root (two levels up from backend/api/)
        self.project_root = Path(__file__).parent.parent.parent.absolute()
        
    def _resolve_path(self, user_path: str) -> Path:
        """
        Resolve user-provided path relative to project root.
        
        Args:
            user_path: Path provided by user (e.g., ".", "frontend", "/absolute/path")
            
        Returns:
            Resolved absolute Path object
        """
        user_path = user_path.strip()
        
        # Handle current directory
        if user_path == '.' or user_path == '':
            return self.project_root
            
        # Convert to Path object
        path = Path(user_path)
        
        # If absolute path, use as-is
        if path.is_absolute():
            return path
            
        # Otherwise resolve relative to project root
        return (self.project_root / path).resolve()
        
    async def get_project_files(
        self, 
        path: str, 
        python_only: bool = True, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get project files from the specified directory.
        
        Args:
            path: Directory path to scan (resolved relative to project root)
            python_only: Only return Python files
            limit: Maximum number of files to return
            
        Returns:
            Dict containing files and metadata
        """
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                return {
                    "error": f"Path does not exist: {path}",
                    "base_path": str(resolved_path),
                    "files": [],
                    "python_file_count": 0,
                    "total_files": 0
                }
                
            if not resolved_path.is_dir():
                return {
                    "error": f"Path is not a directory: {path}",
                    "base_path": str(resolved_path),
                    "files": [],
                    "python_file_count": 0,
                    "total_files": 0
                }
            
            files = []
            python_count = 0
            total_count = 0
            
            # Scan directory
            for item in resolved_path.iterdir():
                if total_count >= limit:
                    break
                    
                if item.is_file():
                    is_python = item.suffix in ['.py', '.pyw', '.pyx']
                    
                    # Skip non-Python files if python_only is True
                    if python_only and not is_python:
                        continue
                    
                    # Get file stats
                    stat = item.stat()
                    
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.project_root)),
                        "type": "file",
                        "size": stat.st_size,
                        "last_modified": stat.st_mtime,
                        "is_python": is_python
                    })
                    
                    if is_python:
                        python_count += 1
                    total_count += 1
                        
            return {
                "base_path": str(resolved_path),
                "files": files,
                "python_file_count": python_count,
                "total_files": total_count,
                "project_root": str(self.project_root)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to scan directory: {str(e)}",
                "base_path": path,
                "files": [],
                "python_file_count": 0,
                "total_files": 0
            }

    async def browse_filesystem(
        self, 
        path: str, 
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        Browse filesystem directory structure.
        
        Args:
            path: Directory path to browse (resolved relative to project root)
            include_hidden: Include hidden files/directories
            
        Returns:
            Dict containing directory contents
        """
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                return {
                    "error": f"Path does not exist: {path}",
                    "current_path": str(resolved_path),
                    "files": [],
                    "directories": []
                }
                
            if not resolved_path.is_dir():
                return {
                    "error": f"Path is not a directory: {path}",
                    "current_path": str(resolved_path),
                    "files": [],
                    "directories": []
                }
            
            files = []
            directories = []
            
            # Scan directory
            for item in resolved_path.iterdir():
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                relative_path = str(item.relative_to(self.project_root))
                stat = item.stat()
                
                if item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": relative_path,
                        "type": "directory",
                        "size": None,
                        "last_modified": stat.st_mtime
                    })
                else:
                    files.append({
                        "name": item.name,
                        "path": relative_path,
                        "type": "file",
                        "size": stat.st_size,
                        "last_modified": stat.st_mtime,
                        "is_python": item.suffix in ['.py', '.pyw', '.pyx']
                    })
            
            # Sort directories and files separately
            directories.sort(key=lambda x: x["name"].lower())
            files.sort(key=lambda x: x["name"].lower())
            
            # Get parent directory
            parent_path = None
            if resolved_path != self.project_root:
                parent = resolved_path.parent
                if parent.is_relative_to(self.project_root):
                    parent_path = str(parent.relative_to(self.project_root)) or "."
                else:
                    parent_path = str(parent)
            
            return {
                "current_path": str(resolved_path.relative_to(self.project_root)) or ".",
                "parent_path": parent_path,
                "files": files,
                "directories": directories,
                "project_root": str(self.project_root)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to browse directory: {str(e)}",
                "current_path": path,
                "files": [],
                "directories": []
            }

    def _create_error_response(self, path: str, resolved_path: Path, error_msg: str) -> Dict[str, Any]:
        """Helper method to create error response for validation."""
        return {
            "valid": False,
            "path": str(resolved_path),
            "exists": False,
            "type": None,
            "readable": False,
            "python_files_count": 0,
            "size": None,
            "error": error_msg,
            "status": "error",
            "project_root": str(self.project_root)
        }

    def _validate_file(self, resolved_path: Path, readable: bool) -> Dict[str, Any]:
        """Helper method to validate a file path."""
        stat = resolved_path.stat()
        return {
            "valid": True,
            "path": str(resolved_path),
            "exists": True,
            "type": "file",
            "readable": readable,
            "python_files_count": 1 if resolved_path.suffix in ['.py', '.pyw', '.pyx'] else 0,
            "size": stat.st_size,
            "status": "success",
            "project_root": str(self.project_root)
        }

    def _validate_directory(self, resolved_path: Path, readable: bool, include_hidden: bool) -> Dict[str, Any]:
        """Helper method to validate a directory path."""
        python_count = 0
        if readable:
            try:
                for item in resolved_path.iterdir():
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    if item.is_file() and item.suffix in ['.py', '.pyw', '.pyx']:
                        python_count += 1
            except PermissionError:
                pass
        
        return {
            "valid": True,
            "path": str(resolved_path),
            "exists": True,
            "type": "directory",
            "readable": readable,
            "python_files_count": python_count,
            "size": None,
            "status": "success",
            "project_root": str(self.project_root)
        }

    async def validate_path(
        self, 
        path: str, 
        include_hidden: bool = False, 
        python_only: bool = False
    ) -> Dict[str, Any]:
        """
        Validate if a path exists and get basic information.
        
        Args:
            path: Path to validate (resolved relative to project root)
            include_hidden: Include hidden files in count
            python_only: Only count Python files
            
        Returns:
            Dict containing validation results
        """
        try:
            resolved_path = self._resolve_path(path)
            
            if not resolved_path.exists():
                return self._create_error_response(
                    path, resolved_path, f"Path does not exist: {path}"
                )
            
            # Check if readable
            readable = os.access(resolved_path, os.R_OK)
            
            if resolved_path.is_file():
                return self._validate_file(resolved_path, readable)
            
            elif resolved_path.is_dir():
                return self._validate_directory(resolved_path, readable, include_hidden)
            
            else:
                return {
                    "valid": False,
                    "path": str(resolved_path),
                    "exists": True,
                    "type": "other",
                    "readable": readable,
                    "python_files_count": 0,
                    "size": None,
                    "error": f"Path is not a regular file or directory: {path}",
                    "status": "error",
                    "project_root": str(self.project_root)
                }
                
        except Exception as e:
            return {
                "valid": False,
                "path": path,
                "exists": False,
                "type": None,
                "readable": False,
                "python_files_count": 0,
                "size": None,
                "error": f"Failed to validate path: {str(e)}",
                "status": "error",
                "project_root": str(self.project_root) if hasattr(self, 'project_root') else 'unknown'
            } 