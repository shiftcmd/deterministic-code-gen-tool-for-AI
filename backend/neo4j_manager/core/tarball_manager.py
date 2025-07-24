"""
Tarball Manager - Handles tarball creation and extraction for Neo4j backups

Provides async-safe tarball operations with progress tracking and error handling.
"""

import asyncio
import logging
import tarfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..models.backup_metadata import TarballResult

logger = logging.getLogger(__name__)


class TarballManager:
    """Manages tarball creation and extraction operations."""
    
    def __init__(self):
        self.compression_types = {
            "gzip": "gz",
            "bzip2": "bz2",
            "xz": "xz",
            "none": ""
        }
    
    async def create_tarball(
        self,
        source_dir: Path,
        target_path: Path,
        compression: str = "gzip",
        exclude_patterns: Optional[List[str]] = None
    ) -> TarballResult:
        """
        Create a tarball from a directory.
        
        Args:
            source_dir: Directory to compress
            target_path: Path for the output tarball
            compression: Compression type (gzip, bzip2, xz, none)
            exclude_patterns: Patterns to exclude from the tarball
        
        Returns:
            TarballResult with operation status
        """
        result = TarballResult(
            operation="create",
            source_path=str(source_dir),
            target_path=str(target_path)
        )
        
        try:
            if not source_dir.exists():
                result.error = f"Source directory does not exist: {source_dir}"
                return result
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine compression mode
            mode = self._get_tar_mode(compression, write=True)
            
            # Create tarball in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._create_tarball_sync,
                source_dir,
                target_path,
                mode,
                exclude_patterns
            )
            
            # Get tarball size
            if target_path.exists():
                result.size_bytes = target_path.stat().st_size
                result.success = True
                logger.info(f"Created tarball: {target_path} ({result.size_bytes / 1024 / 1024:.2f} MB)")
            else:
                result.error = "Tarball creation failed - file not found after operation"
            
            return result
            
        except Exception as e:
            logger.error(f"Tarball creation failed: {e}")
            result.error = str(e)
            return result
    
    async def extract_tarball(
        self,
        tarball_path: Path,
        target_dir: Path,
        verify_before_extract: bool = True
    ) -> TarballResult:
        """
        Extract a tarball to a directory.
        
        Args:
            tarball_path: Path to the tarball file
            target_dir: Directory to extract to
            verify_before_extract: Whether to verify tarball integrity first
        
        Returns:
            TarballResult with operation status
        """
        result = TarballResult(
            operation="extract",
            source_path=str(tarball_path),
            target_path=str(target_dir)
        )
        
        try:
            if not tarball_path.exists():
                result.error = f"Tarball does not exist: {tarball_path}"
                return result
            
            # Verify tarball if requested
            if verify_before_extract:
                verify_result = await self.verify_tarball(tarball_path)
                if not verify_result.success:
                    result.error = f"Tarball verification failed: {verify_result.error}"
                    return result
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._extract_tarball_sync,
                tarball_path,
                target_dir
            )
            
            result.success = True
            result.size_bytes = tarball_path.stat().st_size
            logger.info(f"Extracted tarball: {tarball_path} to {target_dir}")
            
            return result
            
        except Exception as e:
            logger.error(f"Tarball extraction failed: {e}")
            result.error = str(e)
            return result
    
    async def verify_tarball(self, tarball_path: Path) -> TarballResult:
        """
        Verify tarball integrity.
        
        Args:
            tarball_path: Path to the tarball to verify
        
        Returns:
            TarballResult with verification status
        """
        result = TarballResult(
            operation="verify",
            source_path=str(tarball_path)
        )
        
        try:
            if not tarball_path.exists():
                result.error = f"Tarball does not exist: {tarball_path}"
                return result
            
            # Verify in executor
            loop = asyncio.get_event_loop()
            is_valid = await loop.run_in_executor(
                None,
                self._verify_tarball_sync,
                tarball_path
            )
            
            if is_valid:
                result.success = True
                result.size_bytes = tarball_path.stat().st_size
                logger.info(f"Tarball verified successfully: {tarball_path}")
            else:
                result.error = "Tarball is corrupted or invalid"
            
            return result
            
        except Exception as e:
            logger.error(f"Tarball verification failed: {e}")
            result.error = str(e)
            return result
    
    def _get_tar_mode(self, compression: str, write: bool = True) -> str:
        """Get tarfile mode string based on compression type."""
        operation = "w" if write else "r"
        
        if compression == "gzip":
            return f"{operation}:gz"
        elif compression == "bzip2":
            return f"{operation}:bz2"
        elif compression == "xz":
            return f"{operation}:xz"
        else:
            return operation
    
    def _create_tarball_sync(
        self,
        source_dir: Path,
        target_path: Path,
        mode: str,
        exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Synchronous tarball creation."""
        with tarfile.open(target_path, mode) as tar:
            # Add filter function if we have exclude patterns
            if exclude_patterns:
                def filter_func(tarinfo):
                    for pattern in exclude_patterns:
                        if pattern in tarinfo.name:
                            return None
                    return tarinfo
                
                tar.add(source_dir, arcname=source_dir.name, filter=filter_func)
            else:
                tar.add(source_dir, arcname=source_dir.name)
    
    def _extract_tarball_sync(self, tarball_path: Path, target_dir: Path) -> None:
        """Synchronous tarball extraction."""
        with tarfile.open(tarball_path, "r:*") as tar:
            # Extract with security considerations
            tar.extractall(path=target_dir, filter='data')
    
    def _verify_tarball_sync(self, tarball_path: Path) -> bool:
        """Synchronous tarball verification."""
        try:
            with tarfile.open(tarball_path, "r:*") as tar:
                # Try to read the member list
                members = tar.getmembers()
                return len(members) > 0
        except Exception:
            return False
    
    async def list_contents(self, tarball_path: Path) -> Optional[List[str]]:
        """
        List contents of a tarball without extracting.
        
        Args:
            tarball_path: Path to the tarball
        
        Returns:
            List of file paths in the tarball, or None if error
        """
        try:
            loop = asyncio.get_event_loop()
            contents = await loop.run_in_executor(
                None,
                self._list_contents_sync,
                tarball_path
            )
            return contents
        except Exception as e:
            logger.error(f"Failed to list tarball contents: {e}")
            return None
    
    def _list_contents_sync(self, tarball_path: Path) -> List[str]:
        """Synchronous tarball content listing."""
        with tarfile.open(tarball_path, "r:*") as tar:
            return [member.name for member in tar.getmembers()]