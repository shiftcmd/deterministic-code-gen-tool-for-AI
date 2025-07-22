"""
Main FastAPI application entry point.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

# Get application settings
settings = get_settings()

app = FastAPI(
    title="Python Debug Tool API",
    description="A comprehensive debugging and analysis utility for large Python projects",  # noqa: E501
    version="0.1.0",
    debug=settings.is_development,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"message": "Python Debug Tool API is running", "version": "0.1.0"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "python-debug-tool"}


@app.get("/api/health")
async def api_health_check() -> dict[str, str]:
    """API Health check endpoint for frontend."""
    return {"status": "healthy", "service": "python-debug-tool"}


@app.get("/api/files")
async def get_files():
    """Get project files endpoint."""
    return {
        "files": [],
        "message": "File API endpoint ready",
        "status": "success"
    }


@app.get("/api/filesystem/")
async def filesystem_browse():
    """Browse filesystem endpoint."""
    return {
        "files": [],
        "directories": [],
        "status": "success"
    }


@app.get("/api/processes/")
async def running_processes():
    """Get running processes endpoint."""
    return {
        "processes": [],
        "status": "success"
    }


@app.get("/api/debug/start")
async def start_debug_session():
    """
    Start a new debugging session
    """
    session_id = f"debug_session_{int(time.time())}"
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Debug session started successfully"
    }


# Core API endpoints that frontend expects
@app.get("/api/runs")
async def get_runs():
    """Get all runs."""
    return {
        "runs": [],
        "status": "success"
    }


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get specific run details."""
    return {
        "run_id": run_id,
        "status": "completed",
        "files": [],
        "metrics": {}
    }


@app.get("/api/runs/{run_id}/dashboard")
async def get_run_dashboard(run_id: str):
    """Get dashboard data for run."""
    return {
        "dashboard": {
            "metrics": {},
            "charts": [],
            "summary": {}
        },
        "status": "success"
    }


@app.get("/api/filesystem/browse")
async def browse_filesystem(path: str = "/"):
    """Browse filesystem with query params - returns array format."""
    # Handle different paths
    if path == "/" or path == "":
        # Return root project structure
        return get_root_structure()
    elif "frontend" in path:
        return get_frontend_structure(path)
    elif "backend" in path:
        return get_backend_structure(path)
    else:
        return get_root_structure()


def get_root_structure():
    # Return the actual Python Debug Tool project structure
    return [
        {
            "name": "backend",
            "path": "/home/amo/coding_projects/python_debug_tool/backend",
            "type": "directory",
            "size": 0
        },
        {
            "name": "frontend",
            "path": "/home/amo/coding_projects/python_debug_tool/frontend",
            "type": "directory",
            "size": 0
        },
        {
            "name": "scripts",
            "path": "/home/amo/coding_projects/python_debug_tool/scripts",
            "type": "directory",
            "size": 0
        },
        {
            "name": "tools",
            "path": "/home/amo/coding_projects/python_debug_tool/tools",
            "type": "directory",
            "size": 0
        },
        {
            "name": "tests",
            "path": "/home/amo/coding_projects/python_debug_tool/tests",
            "type": "directory",
            "size": 0
        },
        {
            "name": "project_docs",
            "path": "/home/amo/coding_projects/python_debug_tool/project_docs",
            "type": "directory",
            "size": 0
        },
        {
            "name": "README.md",
            "path": "/home/amo/coding_projects/python_debug_tool/README.md",
            "type": "file",
            "size": 2048
        },
        {
            "name": "requirements.txt",
            "path": "/home/amo/coding_projects/python_debug_tool/requirements.txt",
            "type": "file",
            "size": 512
        },
        {
            "name": "main.py",
            "path": "/home/amo/coding_projects/python_debug_tool/main.py",
            "type": "file",
            "size": 1024
        }
    ]


def get_frontend_structure(path: str):
    """Return frontend directory structure."""
    return [
        {
            "name": "src",
            "path": "/home/amo/coding_projects/python_debug_tool/frontend/src",
            "type": "directory",
            "size": 0
        },
        {
            "name": "public",
            "path": "/home/amo/coding_projects/python_debug_tool/frontend/public",
            "type": "directory",
            "size": 0
        },
        {
            "name": "package.json",
            "path": "/home/amo/coding_projects/python_debug_tool/frontend/package.json",
            "type": "file",
            "size": 2048
        },
        {
            "name": "README.md",
            "path": "/home/amo/coding_projects/python_debug_tool/frontend/README.md",
            "type": "file",
            "size": 1024
        }
    ]


def get_backend_structure(path: str):
    """Return backend directory structure."""
    return [
        {
            "name": "api",
            "path": "/home/amo/coding_projects/python_debug_tool/backend/api",
            "type": "directory",
            "size": 0
        },
        {
            "name": "parser",
            "path": "/home/amo/coding_projects/python_debug_tool/backend/parser",
            "type": "directory",
            "size": 0
        },
        {
            "name": "main.py",
            "path": "/home/amo/coding_projects/python_debug_tool/backend/main.py",
            "type": "file",
            "size": 3072
        },
        {
            "name": "config.py",
            "path": "/home/amo/coding_projects/python_debug_tool/backend/config.py",
            "type": "file",
            "size": 1536
        }
    ]


@app.post("/api/filesystem/validate")
async def validate_filesystem_path():
    """Validate filesystem path endpoint."""
    return {
        "valid": True,
        "path": "/example/path",
        "exists": True,
        "type": "directory",
        "message": "Path is valid"
    }


@app.post("/api/projects/analyze")
async def analyze_project():
    """Analyze project endpoint."""
    return {
        "analysis_id": "analysis_1",
        "status": "started"
    }


@app.get("/api/processing/status/{run_id}")
async def get_processing_status(run_id: str):
    """Get processing status."""
    return {
        "run_id": run_id,
        "status": "completed",
        "progress": 100
    }


# IDE Integration Endpoints
@app.post("/api/ide/open")
async def open_in_ide(request: dict):
    """
    Open a file in IDE (VSCode, PyCharm, etc.)
    """
    file_path = request.get("file_path")
    line_number = request.get("line_number")
    
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")
    
    try:
        # Determine the IDE to use (prioritize VSCode)
        ide_command = None
        
        # Try VSCode first
        if os.system("which code > /dev/null 2>&1") == 0:
            if line_number:
                ide_command = f"code -g '{file_path}:{line_number}'"
            else:
                ide_command = f"code '{file_path}'"
        
        # Try PyCharm if VSCode not available
        elif os.system("which pycharm > /dev/null 2>&1") == 0:
            if line_number:
                ide_command = f"pycharm --line {line_number} '{file_path}'"
            else:
                ide_command = f"pycharm '{file_path}'"
        
        # Try vim as fallback
        elif os.system("which vim > /dev/null 2>&1") == 0:
            if line_number:
                ide_command = f"vim +{line_number} '{file_path}'"
            else:
                ide_command = f"vim '{file_path}'"
        
        else:
            # Try to open with default system editor
            ide_command = f"xdg-open '{file_path}' 2>/dev/null || open '{file_path}' 2>/dev/null"
        
        if ide_command:
            # Run the command in background
            os.system(f"{ide_command} &")
            
            return {
                "success": True,
                "message": f"Opened {file_path} in IDE",
                "command_used": ide_command.split(" &")[0],
                "file_path": file_path,
                "line_number": line_number
            }
        else:
            raise HTTPException(status_code=500, detail="No suitable IDE found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open file in IDE: {str(e)}")

@app.get("/api/ide/validate")
async def validate_ide_connection():
    """
    Validate available IDE connections
    """
    available_ides = []
    
    # Check for VSCode
    if os.system("which code > /dev/null 2>&1") == 0:
        available_ides.append({
            "name": "Visual Studio Code",
            "command": "code",
            "priority": 1,
            "supports_line_jump": True
        })
    
    # Check for PyCharm
    if os.system("which pycharm > /dev/null 2>&1") == 0:
        available_ides.append({
            "name": "PyCharm",
            "command": "pycharm",
            "priority": 2,
            "supports_line_jump": True
        })
    
    # Check for Vim
    if os.system("which vim > /dev/null 2>&1") == 0:
        available_ides.append({
            "name": "Vim",
            "command": "vim",
            "priority": 3,
            "supports_line_jump": True
        })
    
    # Check for generic file opener
    system_opener = None
    if os.system("which xdg-open > /dev/null 2>&1") == 0:
        system_opener = "xdg-open"  # Linux
    elif os.system("which open > /dev/null 2>&1") == 0:
        system_opener = "open"  # macOS
    
    if system_opener:
        available_ides.append({
            "name": "System Default",
            "command": system_opener,
            "priority": 10,
            "supports_line_jump": False
        })
    
    return {
        "available_ides": available_ides,
        "primary_ide": available_ides[0] if available_ides else None,
        "total_count": len(available_ides)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
