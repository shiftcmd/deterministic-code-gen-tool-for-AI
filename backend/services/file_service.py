"""
File System Service Layer - Robust Architecture

Uses pyarrow.fs.LocalFileSystem for robust file operations.
Implements proper recursive traversal and analysis directory workflow.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import pyarrow.fs as fs


class FileSystemService:
    """
    Robust file system service using Apache Arrow's LocalFileSystem.
    
    Architecture:
    1. Use pyarrow.fs.LocalFileSystem for robust file operations
    2. Recursive directory traversal with FileSelector
    3. Copy selected files to analysis directory before parsing
    4. Keep original project files untouched
    """
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB default limit
        
        # Get the actual project root (two levels up from backend/services/)
        self.project_root = Path(__file__).parent.parent.parent.absolute()
        
        # Initialize PyArrow LocalFileSystem
        self.arrow_fs = fs.LocalFileSystem()
        
        # Analysis directory for copied files
        self.analysis_dir = self.project_root / ".analysis"
        
    def _resolve_path(self, user_path: str) -> str:
        """
        Resolve user-provided path relative to project root.
        
        Args:
            user_path: Path provided by user (e.g., ".", "./src", "backend/")
            
        Returns:
            Absolute path as string for pyarrow.fs operations
        """
        if user_path == ".":
            return str(self.project_root)
        
        # Handle relative paths
        if not os.path.isabs(user_path):
            resolved = self.project_root / user_path
        else:
            resolved = Path(user_path)
            
        return str(resolved.resolve())
    
    def _create_analysis_session(self, source_path: str) -> str:
        """
        Create a new analysis session directory.
        
        Args:
            source_path: Source directory being analyzed
            
        Returns:
            Analysis session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        session_dir = self.analysis_dir / session_id
        
        # Create analysis directory structure
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "source_files").mkdir(exist_ok=True)
        (session_dir / "metadata").mkdir(exist_ok=True)
        (session_dir / "results").mkdir(exist_ok=True)
        
        # Store session metadata
        metadata = {
            "session_id": session_id,
            "source_path": source_path,
            "created_at": datetime.now().isoformat(),
            "status": "initialized"
        }
        
        metadata_file = session_dir / "metadata" / "session.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return session_id
        
    async def get_project_files(
        self, 
        path: str, 
        python_only: bool = True, 
        limit: int = 1000,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Get project files using recursive traversal with pyarrow.fs.
        
        Args:
            path: Directory path to scan
            python_only: Only return Python files
            limit: Maximum number of files to return
            recursive: Whether to scan recursively (default: True)
            
        Returns:
            Dict containing files and metadata
        """
        try:
            resolved_path = self._resolve_path(path)
            
            # Check if path exists using PyArrow
            try:
                path_info = self.arrow_fs.get_file_info(resolved_path)
                if path_info.type == fs.FileType.NotFound:
                    return {
                        "error": f"Path does not exist: {path}",
                        "resolved_path": resolved_path,
                        "files": [],
                        "python_file_count": 0,
                        "total_files": 0
                    }
                    
                if path_info.type != fs.FileType.Directory:
                    return {
                        "error": f"Path is not a directory: {path}",
                        "resolved_path": resolved_path,
                        "files": [],
                        "python_file_count": 0,
                        "total_files": 0
                    }
            except Exception as e:
                return {
                    "error": f"Failed to access path: {str(e)}",
                    "resolved_path": resolved_path,
                    "files": [],
                    "python_file_count": 0,
                    "total_files": 0
                }
            
            # Use FileSelector for recursive traversal
            selector = fs.FileSelector(resolved_path, recursive=recursive)
            file_infos = self.arrow_fs.get_file_info(selector)
            
            files = []
            python_count = 0
            total_count = 0
            
            for file_info in file_infos:
                # Skip directories
                if file_info.type != fs.FileType.File:
                    continue
                    
                if total_count >= limit:
                    break
                
                # Get file path relative to project root
                rel_path = os.path.relpath(file_info.path, self.project_root)
                
                # Check if it's a Python file
                is_python = any(file_info.path.endswith(ext) for ext in ['.py', '.pyw', '.pyx'])
                
                # Skip non-Python files if python_only is True
                if python_only and not is_python:
                    continue
                
                # Skip files that are too large
                if file_info.size > self.max_file_size:
                    continue
                    
                # Skip hidden files and common non-source directories
                if any(part.startswith('.') for part in rel_path.split(os.sep)):
                    if not any(part in ['.github', '.vscode'] for part in rel_path.split(os.sep)):
                        continue
                
                files.append({
                    "name": os.path.basename(file_info.path),
                    "path": rel_path,
                    "absolute_path": file_info.path,
                    "type": "file",
                    "size": file_info.size,
                    "is_python": is_python,
                    "last_modified": file_info.mtime.timestamp() if file_info.mtime else None
                })
                
                if is_python:
                    python_count += 1
                total_count += 1
            
            return {
                "resolved_path": resolved_path,
                "files": files,
                "python_file_count": python_count,
                "total_files": total_count,
                "recursive": recursive,
                "truncated": total_count >= limit
            }
            
        except Exception as e:
            return {
                "error": f"File system error: {str(e)}",
                "resolved_path": resolved_path if 'resolved_path' in locals() else path,
                "files": [],
                "python_file_count": 0,
                "total_files": 0
            }
    
    async def browse_filesystem(
        self, 
        path: str, 
        include_hidden: bool = False,
        recursive: bool = False,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Browse file system using pyarrow.fs with proper recursive options.
        
        Args:
            path: Directory path to browse
            include_hidden: Include hidden files/directories
            recursive: Whether to scan recursively
            max_depth: Maximum recursion depth if recursive=True
            
        Returns:
            Dict containing directory contents
        """
        try:
            resolved_path = self._resolve_path(path)
            
            # Check if path exists
            try:
                path_info = self.arrow_fs.get_file_info(resolved_path)
                if path_info.type == fs.FileType.NotFound:
                    return {
                        "error": f"Path does not exist: {path}",
                        "current_path": resolved_path,
                        "files": [],
                        "directories": []
                    }
                    
                if path_info.type != fs.FileType.Directory:
                    return {
                        "error": f"Path is not a directory: {path}",
                        "current_path": resolved_path,
                        "files": [],
                        "directories": []
                    }
            except Exception as e:
                return {
                    "error": f"Failed to access path: {str(e)}",
                    "current_path": resolved_path,
                    "files": [],
                    "directories": []
                }
            
            # Use FileSelector for browsing
            selector = fs.FileSelector(resolved_path, recursive=recursive)
            file_infos = self.arrow_fs.get_file_info(selector)
            
            files = []
            directories = []
            
            for file_info in file_infos:
                # Get relative path for display
                rel_path = os.path.relpath(file_info.path, self.project_root)
                
                # Skip hidden files unless requested
                if not include_hidden:
                    if any(part.startswith('.') for part in rel_path.split(os.sep)):
                        continue
                
                # If recursive, check depth
                if recursive:
                    depth = len(os.path.relpath(file_info.path, resolved_path).split(os.sep))
                    if depth > max_depth:
                        continue
                
                if file_info.type == fs.FileType.Directory:
                    directories.append({
                        "name": os.path.basename(file_info.path),
                        "path": rel_path,
                        "absolute_path": file_info.path,
                        "type": "directory",
                        "size": None,
                        "last_modified": file_info.mtime.timestamp() if file_info.mtime else None
                    })
                else:
                    is_python = any(file_info.path.endswith(ext) for ext in ['.py', '.pyw', '.pyx'])
                    files.append({
                        "name": os.path.basename(file_info.path),
                        "path": rel_path,
                        "absolute_path": file_info.path,
                        "type": "file",
                        "size": file_info.size,
                        "last_modified": file_info.mtime.timestamp() if file_info.mtime else None,
                        "is_python": is_python
                    })
            
            return {
                "current_path": resolved_path,
                "files": files,
                "directories": directories,
                "recursive": recursive,
                "include_hidden": include_hidden
            }
            
        except Exception as e:
            return {
                "error": f"File system error: {str(e)}",
                "current_path": resolved_path if 'resolved_path' in locals() else path,
                "files": [],
                "directories": []
            }
    
    async def validate_path(
        self, 
        path: str, 
        include_hidden: bool = False, 
        python_only: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a file system path using pyarrow.fs.
        
        Args:
            path: Path to validate
            include_hidden: Whether to include hidden files (for compatibility)
            python_only: Whether to only consider Python files (for compatibility)
            
        Returns:
            Dict containing validation results
        """
        try:
            resolved_path = self._resolve_path(path)
            
            # Get file info using PyArrow
            file_info = self.arrow_fs.get_file_info(resolved_path)
            
            return {
                "path": path,
                "resolved_path": resolved_path,
                "exists": file_info.type != fs.FileType.NotFound,
                "is_directory": file_info.type == fs.FileType.Directory,
                "is_file": file_info.type == fs.FileType.File,
                "size": file_info.size if file_info.type == fs.FileType.File else None,
                "last_modified": file_info.mtime.timestamp() if file_info.mtime else None
            }
            
        except Exception as e:
            return {
                "path": path,
                "resolved_path": resolved_path if 'resolved_path' in locals() else path,
                "exists": False,
                "error": str(e)
            }
    
    async def copy_files_for_analysis(
        self, 
        source_path: str, 
        file_patterns: List[str] | None = None,
        python_only: bool = True
    ) -> Dict[str, Any]:
        """
        Copy selected files to analysis directory for safe processing.
        
        Args:
            source_path: Source directory to copy from
            file_patterns: List of file patterns to include (e.g., ["*.py", "*.pyx"])
            python_only: Only copy Python files
            
        Returns:
            Dict with analysis session info and copied files
        """
        try:
            resolved_source = self._resolve_path(source_path)
            
            # Create analysis session
            session_id = self._create_analysis_session(resolved_source)
            session_dir = self.analysis_dir / session_id
            source_dir = session_dir / "source_files"
            
            # Get files to copy
            files_info = await self.get_project_files(
                source_path, 
                python_only=python_only, 
                recursive=True,
                limit=5000  # Higher limit for analysis
            )
            
            if "error" in files_info:
                return {
                    "error": files_info["error"],
                    "session_id": None
                }
            
            # Copy files using PyArrow's copy functionality
            copied_files = []
            failed_files = []
            
            for file_info in files_info["files"]:
                try:
                    source_file = file_info["absolute_path"]
                    
                    # Create relative directory structure in analysis dir
                    rel_path = file_info["path"]
                    dest_file = source_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file using pyarrow
                    self.arrow_fs.copy_file(source_file, str(dest_file))
                    
                    copied_files.append({
                        "source": source_file,
                        "destination": str(dest_file),
                        "relative_path": rel_path,
                        "size": file_info["size"]
                    })
                    
                except Exception as e:
                    failed_files.append({
                        "file": file_info["path"],
                        "error": str(e)
                    })
            
            # Update session metadata
            metadata_file = session_dir / "metadata" / "session.json"
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata.update({
                "status": "files_copied",
                "copied_files_count": len(copied_files),
                "failed_files_count": len(failed_files),
                "copy_completed_at": datetime.now().isoformat()
            })
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "session_id": session_id,
                "analysis_directory": str(session_dir),
                "source_files_directory": str(source_dir),
                "copied_files": copied_files,
                "failed_files": failed_files,
                "total_copied": len(copied_files),
                "total_failed": len(failed_files)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to copy files for analysis: {str(e)}",
                "session_id": None
            } 