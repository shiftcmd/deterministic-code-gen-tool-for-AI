"""
IDE integration routes for the Python Debug Tool API.

This module provides endpoints for integrating with various IDEs and editors.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["ide"])


class IDEOpenRequest(BaseModel):
    """Request model for opening files in IDE."""
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    preferred_ide: Optional[str] = None


class IDEInfo(BaseModel):
    """IDE information model."""
    name: str
    command: str
    priority: int
    supports_line_jump: bool
    available: bool = False


def check_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        result = subprocess.run(
            ["which", command], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_available_ides() -> List[IDEInfo]:
    """Get list of available IDEs on the system."""
    
    # Define known IDEs and their commands
    known_ides = [
        IDEInfo(
            name="Visual Studio Code",
            command="code",
            priority=1,
            supports_line_jump=True
        ),
        IDEInfo(
            name="PyCharm",
            command="pycharm",
            priority=2,
            supports_line_jump=True
        ),
        IDEInfo(
            name="Sublime Text",
            command="subl",
            priority=3,
            supports_line_jump=True
        ),
        IDEInfo(
            name="Atom",
            command="atom",
            priority=4,
            supports_line_jump=True
        ),
        IDEInfo(
            name="Vim",
            command="vim",
            priority=5,
            supports_line_jump=True
        ),
        IDEInfo(
            name="Emacs",
            command="emacs",
            priority=6,
            supports_line_jump=True
        ),
        IDEInfo(
            name="Nano",
            command="nano",
            priority=7,
            supports_line_jump=False
        )
    ]
    
    # Check availability
    available_ides = []
    for ide in known_ides:
        ide.available = check_command_available(ide.command)
        if ide.available:
            available_ides.append(ide)
    
    # Add system default opener if available
    system_opener = None
    if check_command_available("xdg-open"):
        system_opener = "xdg-open"  # Linux
    elif check_command_available("open"):
        system_opener = "open"  # macOS
    elif check_command_available("start"):
        system_opener = "start"  # Windows
    
    if system_opener:
        available_ides.append(IDEInfo(
            name="System Default",
            command=system_opener,
            priority=10,
            supports_line_jump=False,
            available=True
        ))
    
    return sorted(available_ides, key=lambda x: x.priority)


@router.get("/ide/validate")
async def validate_ide_connection() -> Dict[str, Any]:
    """Validate available IDE connections."""
    
    available_ides = get_available_ides()
    
    return {
        "available_ides": [ide.dict() for ide in available_ides],
        "primary_ide": available_ides[0].dict() if available_ides else None,
        "total_count": len(available_ides),
        "system_info": {
            "platform": os.name,
            "path_separator": os.pathsep
        }
    }


@router.post("/ide/open")
async def open_in_ide(request: IDEOpenRequest) -> Dict[str, Any]:
    """Open a file in an IDE or editor."""
    
    try:
        # Validate file path
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {request.file_path}")
        
        # Get available IDEs
        available_ides = get_available_ides()
        if not available_ides:
            raise HTTPException(status_code=503, detail="No IDEs or editors available on this system")
        
        # Select IDE to use
        selected_ide = None
        
        # Try preferred IDE first
        if request.preferred_ide:
            for ide in available_ides:
                if ide.command == request.preferred_ide or ide.name.lower() == request.preferred_ide.lower():
                    selected_ide = ide
                    break
        
        # Fall back to highest priority IDE
        if not selected_ide:
            selected_ide = available_ides[0]
        
        # Build command
        command_args = [selected_ide.command]
        
        # Add line/column jumping if supported
        if request.line_number and selected_ide.supports_line_jump:
            if selected_ide.command == "code":
                # VS Code: code -g file:line:column
                location = f"{file_path}:{request.line_number}"
                if request.column_number:
                    location += f":{request.column_number}"
                command_args.extend(["-g", location])
            elif selected_ide.command == "pycharm":
                # PyCharm: pycharm --line line file
                command_args.extend(["--line", str(request.line_number), str(file_path)])
            elif selected_ide.command == "subl":
                # Sublime: subl file:line:column
                location = f"{file_path}:{request.line_number}"
                if request.column_number:
                    location += f":{request.column_number}"
                command_args.append(location)
            elif selected_ide.command == "vim":
                # Vim: vim +line file
                command_args.extend([f"+{request.line_number}", str(file_path)])
            elif selected_ide.command == "emacs":
                # Emacs: emacs +line:column file
                location = f"+{request.line_number}"
                if request.column_number:
                    location += f":{request.column_number}"
                command_args.extend([location, str(file_path)])
            else:
                # Generic: just open the file
                command_args.append(str(file_path))
        else:
            # Just open the file
            command_args.append(str(file_path))
        
        # Execute command
        try:
            result = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "ide_used": selected_ide.name,
                "command": selected_ide.command,
                "file_path": str(file_path),
                "line_number": request.line_number,
                "column_number": request.column_number,
                "return_code": result.returncode,
                "stdout": result.stdout if result.stdout else None,
                "stderr": result.stderr if result.stderr else None,
                "message": "File opened successfully" if success else "Failed to open file"
            }
            
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="IDE command timed out")
        except subprocess.SubprocessError as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute IDE command: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error opening file in IDE: {str(e)}")


@router.get("/ide/preferences")
async def get_ide_preferences() -> Dict[str, Any]:
    """Get IDE preferences and settings."""
    
    available_ides = get_available_ides()
    
    # Determine recommended IDE
    recommended = None
    if available_ides:
        # Prefer VS Code if available
        for ide in available_ides:
            if ide.command == "code":
                recommended = ide
                break
        # Fall back to highest priority
        if not recommended:
            recommended = available_ides[0]
    
    return {
        "available_ides": [ide.dict() for ide in available_ides],
        "recommended": recommended.dict() if recommended else None,
        "preferences": {
            "auto_line_jump": True,
            "preferred_ide": recommended.command if recommended else None,
            "fallback_to_system": True
        }
    }


@router.post("/ide/preferences")
async def set_ide_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Set IDE preferences (placeholder - would need persistent storage)."""
    
    # In a real implementation, this would save to a config file or database
    return {
        "message": "IDE preferences updated (Note: preferences are not persisted in this implementation)",
        "preferences": preferences,
        "status": "success"
    } 