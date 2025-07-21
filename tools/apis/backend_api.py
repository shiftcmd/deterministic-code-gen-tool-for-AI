#!/usr/bin/env python3
"""
Backend API for Deterministic AI Framework Frontend

FastAPI server that provides REST endpoints for the React frontend.
Handles project analysis, processing management, and data storage.
"""

import os
import json
import uuid
import sqlite3
import asyncio
import subprocess
import threading
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
import uvicorn
import traceback

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('framework_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models
class ProjectAnalysisRequest(BaseModel):
    path: str
    isGitRepo: bool = False

class GitCloneRequest(BaseModel):
    repoUrl: str
    targetPath: str

class ProcessingStartRequest(BaseModel):
    projectPath: str
    selectedFiles: List[str]
    isGitRepo: bool = False
    options: Dict[str, Any] = Field(default_factory=dict)

class Neo4jQuery(BaseModel):
    query: str

# Database setup
class DatabaseManager:
    def __init__(self, db_path: str = "framework_runs.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    project_path TEXT NOT NULL,
                    project_name TEXT,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    file_count INTEGER,
                    selected_files TEXT,
                    error TEXT,
                    neo4j_data_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS run_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS framework_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type TEXT DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default configuration values
            default_configs = [
                ('neo4j_host', 'localhost', 'string', 'Neo4j database host'),
                ('neo4j_port', '7687', 'integer', 'Neo4j database port'),
                ('neo4j_database', 'neo4j', 'string', 'Neo4j database name'),
                ('neo4j_username', 'neo4j', 'string', 'Neo4j username'),
                ('neo4j_data_dir', '/var/lib/neo4j/data', 'string', 'Neo4j data directory'),
                ('project_exports_dir', './exports', 'string', 'Directory for exported project data'),
                ('max_file_size_mb', '10', 'integer', 'Maximum file size for analysis (MB)'),
                ('enable_hallucination_detection', 'true', 'boolean', 'Enable AI hallucination detection'),
                ('enable_neo4j_export', 'true', 'boolean', 'Enable Neo4j knowledge graph export'),
                ('processing_timeout_minutes', '30', 'integer', 'Processing timeout in minutes')
            ]
            
            for config_key, config_value, config_type, description in default_configs:
                conn.execute("""
                    INSERT OR IGNORE INTO framework_config 
                    (config_key, config_value, config_type, description)
                    VALUES (?, ?, ?, ?)
                """, (config_key, config_value, config_type, description))
    
    def create_run(self, project_path: str, selected_files: List[str]) -> str:
        """Create a new analysis run"""
        run_id = str(uuid.uuid4())
        
        # Extract project name from path
        project_name = Path(project_path).name
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO runs (id, project_path, project_name, status, started_at, file_count, selected_files)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                project_path,
                project_name,
                'starting',
                datetime.now().isoformat(),
                len(selected_files),
                json.dumps(selected_files)
            ))
        
        return run_id
    
    def update_run(self, run_id: str, **kwargs):
        """Update run status and other fields"""
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        if set_clauses:
            values.append(run_id)
            query = f"UPDATE runs SET {', '.join(set_clauses)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, values)
    
    def get_run(self, run_id: str) -> Optional[Dict]:
        """Get run by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
        return None
    
    def get_runs(self, limit: int = 50) -> List[Dict]:
        """Get all runs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM runs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_result(self, run_id: str, result_type: str, result_data: Any):
        """Save analysis result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO run_results (run_id, result_type, result_data)
                VALUES (?, ?, ?)
            """, (run_id, result_type, json.dumps(result_data)))
    
    def get_results(self, run_id: str) -> Dict[str, Any]:
        """Get all results for a run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT result_type, result_data 
                FROM run_results 
                WHERE run_id = ?
            """, (run_id,))
            
            results = {}
            for row in cursor.fetchall():
                results[row['result_type']] = json.loads(row['result_data'])
            
            return results
    
    def add_log(self, run_id: str, level: str, message: str):
        """Add processing log"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO processing_logs (run_id, level, message)
                VALUES (?, ?, ?)
            """, (run_id, level, message))
    
    def get_config(self, config_key: str) -> Optional[str]:
        """Get configuration value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT config_value FROM framework_config 
                WHERE config_key = ?
            """, (config_key,))
            row = cursor.fetchone()
            return row['config_value'] if row else None
    
    def set_config(self, config_key: str, config_value: str, config_type: str = 'string', description: str = None):
        """Set configuration value"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO framework_config 
                (config_key, config_value, config_type, description, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (config_key, config_value, config_type, description))
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT config_key, config_value, config_type, description 
                FROM framework_config 
                ORDER BY config_key
            """)
            
            config = {}
            for row in cursor.fetchall():
                value = row['config_value']
                # Convert based on type
                if row['config_type'] == 'integer':
                    value = int(value)
                elif row['config_type'] == 'boolean':
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif row['config_type'] == 'float':
                    value = float(value)
                
                config[row['config_key']] = {
                    'value': value,
                    'type': row['config_type'],
                    'description': row['description']
                }
            
            return config
    
    def update_neo4j_data_path(self, run_id: str, neo4j_data_path: str):
        """Update the Neo4j data path for a run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE runs SET neo4j_data_path = ? WHERE id = ?
            """, (neo4j_data_path, run_id))


# Processing manager
class ProcessingManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.process_status: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
    
    async def start_processing(self, run_id: str, project_path: str, selected_files: List[str]) -> None:
        """Start framework processing in background"""
        try:
            self.db.update_run(run_id, status='running')
            self.db.add_log(run_id, 'INFO', f'Starting analysis of {len(selected_files)} files')
            
            # Create file list for processing
            file_list_path = f"/tmp/framework_files_{run_id}.txt"
            with open(file_list_path, 'w') as f:
                for file_path in selected_files:
                    f.write(f"{file_path}\n")
            
            # Start the framework analysis
            cmd = [
                'python3', 'run_full_framework.py',
                '--project-path', project_path,
                '--file-list', file_list_path,
                '--run-id', run_id,
                '--output-format', 'json'
            ]
            
            logger.info(f"Starting framework with command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.active_processes[run_id] = process
            self.process_status[run_id] = {
                'status': 'running',
                'progress': 0,
                'current_phase': 'discovery',
                'logs': []
            }
            
            # Monitor process in background
            threading.Thread(
                target=self._monitor_process,
                args=(run_id, process, selected_files),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Failed to start processing {run_id}: {e}")
            self.db.update_run(run_id, status='failed', error=str(e))
            self.db.add_log(run_id, 'ERROR', f'Failed to start: {e}')
    
    def _monitor_process(self, run_id: str, process: subprocess.Popen, selected_files: List[str]):
        """Monitor running process and update status"""
        try:
            total_files = len(selected_files)
            start_time = time.time()
            
            # Define analysis phases for progress tracking
            phases = [
                ('discovery', 'File Discovery', 10),
                ('parsing', 'AST Parsing', 30),
                ('analysis', 'Code Analysis', 70),
                ('validation', 'Validation', 85),
                ('export', 'Knowledge Graph Export', 95)
            ]
            
            current_phase_index = 0
            
            self.process_status[run_id]['current_phase'] = 'discovery'
            self.process_status[run_id]['progress'] = 5
            self.db.add_log(run_id, 'INFO', f'Framework process started (PID: {process.pid})')
            
            # Monitor the actual process output in real-time
            while process.poll() is None:
                elapsed_time = time.time() - start_time
                
                try:
                    # Read output line by line if available
                    if process.stdout and process.stdout.readable():
                        import select
                        if select.select([process.stdout], [], [], 0.1)[0]:
                            line = process.stdout.readline()
                            if line:
                                log_message = line.decode().strip()
                                if log_message:
                                    # Add to logs
                                    self.process_status[run_id]['logs'].append({
                                        'timestamp': datetime.now().isoformat(),
                                        'level': 'INFO',
                                        'message': log_message
                                    })
                                    self.db.add_log(run_id, 'INFO', log_message)
                    
                    # Simulate progressive phases based on elapsed time
                    if process.poll() is None:
                        # Simulate phase progression every 0.3 seconds
                        phase_duration = 0.3  # seconds per phase
                        target_phase_index = min(int(elapsed_time / phase_duration), len(phases) - 1)
                        
                        if target_phase_index != current_phase_index and target_phase_index < len(phases):
                            current_phase_index = target_phase_index
                            phase_key, phase_name, phase_progress = phases[current_phase_index]
                            
                            self.process_status[run_id]['current_phase'] = phase_key
                            self.process_status[run_id]['progress'] = phase_progress
                            
                            self.db.add_log(run_id, 'INFO', f'Starting phase: {phase_name}')
                        
                        # Wait a bit before next check
                        threading.Event().wait(0.2)
                    
                except Exception as monitor_error:
                    logger.warning(f"Error reading process output: {monitor_error}")
                    threading.Event().wait(0.5)
            
            # Process has finished, get final output
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Process completed successfully
                self.process_status[run_id]['status'] = 'completed'
                self.process_status[run_id]['progress'] = 100
                self.process_status[run_id]['current_phase'] = 'completed'
                
                self.db.update_run(
                    run_id,
                    status='completed',
                    completed_at=datetime.now().isoformat()
                )
                self.db.add_log(run_id, 'INFO', 'Analysis completed successfully')
                
                # Log final output
                if stdout:
                    final_output = stdout.strip() if isinstance(stdout, str) else stdout.decode().strip()
                    if final_output:
                        self.db.add_log(run_id, 'INFO', f'Framework output: {final_output[-500:]}')  # Last 500 chars
                
                # Load and save results
                self._load_results(run_id)
                
            else:
                # Process failed
                error_msg = stderr.strip() if isinstance(stderr, str) else (stderr.decode() if stderr else f"Process exited with code {process.returncode}")
                self.process_status[run_id]['status'] = 'failed'
                self.process_status[run_id]['current_phase'] = 'failed'
                
                self.db.update_run(run_id, status='failed', error=error_msg)
                self.db.add_log(run_id, 'ERROR', f'Analysis failed: {error_msg}')
                
                logger.error(f"Framework process failed for run {run_id}: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error monitoring process {run_id}: {e}")
            self.process_status[run_id]['status'] = 'failed'
            self.process_status[run_id]['current_phase'] = 'error'
            self.db.update_run(run_id, status='failed', error=str(e))
            self.db.add_log(run_id, 'ERROR', f'Monitoring error: {str(e)}')
        
        finally:
            # Cleanup
            if run_id in self.active_processes:
                del self.active_processes[run_id]
    
    def _load_results(self, run_id: str):
        """Load analysis results from files"""
        try:
            logger.info(f"Loading results for run {run_id}")
            
            # Load main analysis results
            results_file = f"full_framework_analysis_{run_id}.json"
            if os.path.exists(results_file):
                logger.info(f"Loading main analysis from {results_file}")
                with open(results_file, 'r') as f:
                    results = json.load(f)
                self.db.save_result(run_id, 'main_analysis', results)
                logger.info(f"Saved main analysis results for run {run_id}")
            else:
                logger.warning(f"Main analysis file not found: {results_file}")
            
            # Load actionable report
            actionable_file = f"actionable_framework_report_{run_id}.json"
            if os.path.exists(actionable_file):
                logger.info(f"Loading actionable report from {actionable_file}")
                with open(actionable_file, 'r') as f:
                    actionable = json.load(f)
                self.db.save_result(run_id, 'actionable_report', actionable)
                logger.info(f"Saved actionable report for run {run_id}")
            else:
                logger.warning(f"Actionable report file not found: {actionable_file}")
            
            # Copy Neo4j data after analysis completion
            self._copy_neo4j_data(run_id)
            
        except Exception as e:
            logger.error(f"Failed to load results for {run_id}: {e}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _copy_neo4j_data(self, run_id: str):
        """Copy Neo4j data folder to project exports directory"""
        try:
            # Get configuration
            neo4j_data_dir = self.db.get_config('neo4j_data_dir') or '/var/lib/neo4j/data'
            exports_dir = self.db.get_config('project_exports_dir') or './exports'
            
            # Get run details
            run = self.db.get_run(run_id)
            if not run:
                logger.error(f"Run {run_id} not found for Neo4j data copy")
                return
            
            # Create project name from path
            project_path = Path(run['project_path'])
            project_name = project_path.name.replace(' ', '_').replace('-', '_')
            
            # Create exports directory structure
            exports_path = Path(exports_dir)
            exports_path.mkdir(parents=True, exist_ok=True)
            
            # Create project-specific directory
            project_export_dir = exports_path / f"{project_name}_{run_id[:8]}"
            project_export_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy Neo4j data
            neo4j_source = Path(neo4j_data_dir)
            neo4j_dest = project_export_dir / "neo4j_data"
            
            if neo4j_source.exists():
                logger.info(f"Copying Neo4j data from {neo4j_source} to {neo4j_dest}")
                shutil.copytree(neo4j_source, neo4j_dest, dirs_exist_ok=True)
                
                # Update run record with Neo4j data path
                self.db.update_neo4j_data_path(run_id, str(neo4j_dest))
                
                # Create metadata file
                metadata = {
                    'run_id': run_id,
                    'project_name': project_name,
                    'project_path': run['project_path'],
                    'neo4j_data_path': str(neo4j_dest),
                    'exported_at': datetime.now().isoformat(),
                    'file_count': run['file_count'],
                    'started_at': run['started_at'],
                    'completed_at': run['completed_at']
                }
                
                metadata_file = project_export_dir / "export_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Copy analysis results to export directory
                for result_file in [f"full_framework_analysis_{run_id}.json", 
                                  f"actionable_framework_report_{run_id}.json"]:
                    if os.path.exists(result_file):
                        shutil.copy2(result_file, project_export_dir)
                
                logger.info(f"Neo4j data successfully exported to {project_export_dir}")
                self.db.add_log(run_id, 'INFO', f'Neo4j data exported to {project_export_dir}')
                
            else:
                logger.warning(f"Neo4j data directory not found: {neo4j_source}")
                self.db.add_log(run_id, 'WARNING', f'Neo4j data directory not found: {neo4j_source}')
                
        except Exception as e:
            logger.error(f"Failed to copy Neo4j data for {run_id}: {e}")
            self.db.add_log(run_id, 'ERROR', f'Failed to copy Neo4j data: {e}')
    
    async def _notify_websockets(self, run_id: str):
        """Notify WebSocket connections of status update"""
        if run_id in self.websocket_connections:
            status = self.process_status.get(run_id, {})
            message = json.dumps(status)
            
            disconnected = []
            for websocket in self.websocket_connections[run_id]:
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.websocket_connections[run_id].remove(ws)
    
    def get_status(self, run_id: str) -> Dict:
        """Get current processing status"""
        return self.process_status.get(run_id, {
            'status': 'unknown',
            'progress': 0,
            'current_phase': '',
            'logs': []
        })
    
    def stop_processing(self, run_id: str) -> bool:
        """Stop running process"""
        if run_id in self.active_processes:
            try:
                process = self.active_processes[run_id]
                process.terminate()
                process.wait(timeout=10)
                
                self.db.update_run(run_id, status='stopped')
                self.db.add_log(run_id, 'INFO', 'Analysis stopped by user')
                
                return True
            except Exception as e:
                logger.error(f"Failed to stop process {run_id}: {e}")
        
        return False


# Exception handling middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        logger.info(f"Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Response: {response.status_code} - Duration: {duration:.3f}s")
            return response
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Request failed: {request.method} {request.url}")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Duration: {duration:.3f}s")
            raise

# FastAPI app
app = FastAPI(title="Deterministic AI Framework API", version="1.0.0")

# Add middleware
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://127.0.0.1:3002"
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
db_manager = DatabaseManager()
processing_manager = ProcessingManager(db_manager)

@app.get("/")
async def root():
    return {"message": "Deterministic AI Framework API", "version": "1.0.0"}

@app.post("/api/projects/analyze")
async def analyze_project(request: ProjectAnalysisRequest):
    """Analyze project structure and return file tree"""
    try:
        project_path = Path(request.path)
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project path does not exist")
        
        if not project_path.is_dir():
            raise HTTPException(status_code=400, detail="Path must be a directory")
        
        # Discover Python files
        python_files = []
        directories = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip common excluded directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            root_path = Path(root)
            rel_root = root_path.relative_to(project_path)
            
            if str(rel_root) != '.':
                directories.append({
                    'path': str(rel_root),
                    'name': root_path.name,
                    'type': 'directory'
                })
            
            for file in files:
                if file.endswith(('.py', '.pyi')):
                    file_path = root_path / file
                    rel_path = file_path.relative_to(project_path)
                    
                    try:
                        stat_info = file_path.stat()
                        python_files.append({
                            'path': str(rel_path),
                            'name': file,
                            'type': 'file',
                            'size': stat_info.st_size,
                            'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                        })
                    except:
                        pass
        
        return {
            'path': str(project_path),
            'isGitRepo': request.isGitRepo,
            'files': python_files,
            'directories': directories,
            'stats': {
                'total_files': len(python_files),
                'total_directories': len(directories)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/clone")
async def clone_git_repo(request: GitCloneRequest):
    """Clone Git repository"""
    try:
        target_path = Path(request.targetPath)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Clone repository
        process = subprocess.run(
            ['git', 'clone', request.repoUrl, str(target_path)],
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Git clone failed: {process.stderr}")
        
        return {
            'path': str(target_path),
            'message': 'Repository cloned successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processing/start")
async def start_processing(request: ProcessingStartRequest, background_tasks: BackgroundTasks):
    """Start framework processing"""
    try:
        # Create new run
        run_id = db_manager.create_run(request.projectPath, request.selectedFiles)
        
        # Start processing in background
        background_tasks.add_task(
            processing_manager.start_processing,
            run_id,
            request.projectPath,
            request.selectedFiles
        )
        
        return {
            'id': run_id,
            'status': 'starting',
            'message': 'Analysis started'
        }
        
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processing/status/{run_id}")
async def get_processing_status(run_id: str):
    """Get processing status"""
    try:
        return processing_manager.get_status(run_id)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/processing/stop/{run_id}")
async def stop_processing(run_id: str):
    """Stop processing"""
    try:
        success = processing_manager.stop_processing(run_id)
        return {'success': success}
    except Exception as e:
        logger.error(f"Failed to stop processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs")
async def get_runs():
    """Get all analysis runs"""
    try:
        runs = db_manager.get_runs()
        return runs
    except Exception as e:
        logger.error(f"Failed to get runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get specific run"""
    try:
        run = db_manager.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run
    except Exception as e:
        logger.error(f"Failed to get run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs/{run_id}/dashboard")
async def get_run_dashboard(run_id: str):
    """Get dashboard data for run"""
    try:
        results = db_manager.get_results(run_id)
        return results
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str):
    """Delete a run and its results"""
    try:
        with sqlite3.connect(db_manager.db_path) as conn:
            # Delete results first (foreign key constraint)
            conn.execute("DELETE FROM run_results WHERE run_id = ?", (run_id,))
            conn.execute("DELETE FROM processing_logs WHERE run_id = ?", (run_id,))
            # Delete the run
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        
        return {"success": True, "message": "Run deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filesystem/validate")
async def validate_path(request: dict):
    """Validate if a path exists and is accessible"""
    try:
        path = request.get("path")
        if not path:
            raise HTTPException(status_code=400, detail="Path is required")
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return {"valid": False, "message": "Path does not exist"}
        
        if not path_obj.is_dir():
            return {"valid": False, "message": "Path is not a directory"}
        
        # Check if it contains Python files
        python_files = list(path_obj.rglob("*.py"))
        if not python_files:
            return {"valid": False, "message": "No Python files found in directory"}
        
        return {"valid": True, "message": "Path is valid", "python_files": len(python_files)}
        
    except Exception as e:
        logger.error(f"Failed to validate path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Neo4j endpoints (placeholder implementations)
@app.get("/api/neo4j/{run_id}/schema")
async def get_neo4j_schema(run_id: str):
    """Get Neo4j schema for a run"""
    try:
        # Placeholder implementation - would connect to actual Neo4j
        return {
            "node_count": 150,
            "relationship_count": 300,
            "node_types": [
                {"label": "File", "count": 50},
                {"label": "Class", "count": 30},
                {"label": "Function", "count": 60},
                {"label": "Issue", "count": 10}
            ],
            "relationship_types": [
                {"type": "CONTAINS", "count": 80},
                {"type": "CALLS", "count": 120},
                {"type": "INHERITS_FROM", "count": 15},
                {"type": "HAS_ISSUE", "count": 85}
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get Neo4j schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/neo4j/{run_id}/query")
async def execute_neo4j_query(run_id: str, request: Neo4jQuery):
    """Execute Cypher query"""
    try:
        logger.info(f"Executing Neo4j query for run {run_id}: {request.query}")
        # Placeholder implementation - would execute actual Cypher query
        return {
            "columns": ["path", "risk_level", "lines_of_code"],
            "records": [
                {"path": "src/main.py", "risk_level": "medium", "lines_of_code": 150},
                {"path": "src/utils.py", "risk_level": "low", "lines_of_code": 80},
                {"path": "src/models.py", "risk_level": "high", "lines_of_code": 200}
            ],
            "query_time": "0.042s"
        }
    except Exception as e:
        logger.error(f"Failed to execute Neo4j query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neo4j/{run_id}/file/{file_path:path}")
async def get_file_analysis(run_id: str, file_path: str):
    """Get detailed analysis for a specific file"""
    try:
        logger.info(f"Getting file analysis for {file_path} in run {run_id}")
        
        # Placeholder implementation - would query Neo4j for file details
        file_analysis = {
            "file_path": file_path,
            "run_id": run_id,
            "node_data": {
                "id": f"file_{file_path.replace('/', '_')}",
                "labels": ["File"],
                "properties": {
                    "path": file_path,
                    "name": file_path.split('/')[-1],
                    "extension": file_path.split('.')[-1] if '.' in file_path else "",
                    "lines_of_code": 156,
                    "risk_level": "medium",
                    "complexity_score": 7.2,
                    "last_modified": "2024-07-21T10:30:00Z"
                }
            },
            "classes": [
                {
                    "name": "DataProcessor",
                    "line_start": 15,
                    "line_end": 45,
                    "methods": ["__init__", "process", "validate"],
                    "complexity": "medium",
                    "relationships": ["INHERITS_FROM:BaseProcessor"]
                },
                {
                    "name": "ConfigManager", 
                    "line_start": 50,
                    "line_end": 80,
                    "methods": ["load_config", "save_config", "get_setting"],
                    "complexity": "low",
                    "relationships": []
                }
            ],
            "functions": [
                {
                    "name": "initialize_system",
                    "line_start": 10,
                    "line_end": 14,
                    "parameters": ["config_path", "debug"],
                    "complexity": "low",
                    "calls": ["load_config", "setup_logging"]
                },
                {
                    "name": "cleanup_resources",
                    "line_start": 85,
                    "line_end": 95,
                    "parameters": [],
                    "complexity": "low", 
                    "calls": ["close_connections", "clear_cache"]
                }
            ],
            "imports": [
                {"module": "os", "type": "standard"},
                {"module": "sys", "type": "standard"},
                {"module": "pandas", "type": "third_party"},
                {"module": ".utils", "type": "local"}
            ],
            "relationships": {
                "depends_on": [
                    {
                        "file": "src/utils.py",
                        "type": "IMPORTS",
                        "strength": "strong",
                        "details": "imports utility functions"
                    },
                    {
                        "file": "src/config.py", 
                        "type": "USES",
                        "strength": "medium",
                        "details": "uses ConfigManager class"
                    }
                ],
                "used_by": [
                    {
                        "file": "src/main.py",
                        "type": "IMPORTS",
                        "strength": "strong", 
                        "details": "main entry point imports this module"
                    },
                    {
                        "file": "tests/test_processor.py",
                        "type": "TESTS",
                        "strength": "medium",
                        "details": "test file for this module"
                    }
                ]
            },
            "issues": [
                {
                    "type": "complexity",
                    "severity": "medium",
                    "line": 25,
                    "message": "Function has high cyclomatic complexity",
                    "recommendation": "Consider breaking into smaller functions"
                },
                {
                    "type": "security",
                    "severity": "low",
                    "line": 60,
                    "message": "Potential path traversal vulnerability",
                    "recommendation": "Validate file paths before use"
                }
            ]
        }
        
        return file_analysis
        
    except Exception as e:
        logger.error(f"Failed to get file analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neo4j/{run_id}/files")
async def get_project_files(run_id: str):
    """Get all files in the project with basic analysis data"""
    try:
        logger.info(f"Getting project files for run {run_id}")
        
        # Placeholder implementation - would query Neo4j for all files
        project_files = {
            "run_id": run_id,
            "total_files": 15,
            "files": [
                {
                    "path": "src/main.py",
                    "name": "main.py",
                    "type": "python",
                    "size": 2048,
                    "lines_of_code": 89,
                    "risk_level": "low",
                    "complexity_score": 4.2,
                    "class_count": 1,
                    "function_count": 3,
                    "import_count": 5,
                    "has_issues": False
                },
                {
                    "path": "src/data_processor.py", 
                    "name": "data_processor.py",
                    "type": "python",
                    "size": 4096,
                    "lines_of_code": 156,
                    "risk_level": "medium",
                    "complexity_score": 7.2,
                    "class_count": 2,
                    "function_count": 8,
                    "import_count": 7,
                    "has_issues": True
                },
                {
                    "path": "src/utils.py",
                    "name": "utils.py", 
                    "type": "python",
                    "size": 1536,
                    "lines_of_code": 67,
                    "risk_level": "low",
                    "complexity_score": 3.1,
                    "class_count": 0,
                    "function_count": 12,
                    "import_count": 3,
                    "has_issues": False
                },
                {
                    "path": "src/config.py",
                    "name": "config.py",
                    "type": "python", 
                    "size": 1024,
                    "lines_of_code": 45,
                    "risk_level": "low",
                    "complexity_score": 2.8,
                    "class_count": 1,
                    "function_count": 4,
                    "import_count": 2,
                    "has_issues": False
                },
                {
                    "path": "tests/test_processor.py",
                    "name": "test_processor.py",
                    "type": "python",
                    "size": 3072,
                    "lines_of_code": 123,
                    "risk_level": "low", 
                    "complexity_score": 5.5,
                    "class_count": 3,
                    "function_count": 15,
                    "import_count": 8,
                    "has_issues": False
                }
            ]
        }
        
        return project_files
        
    except Exception as e:
        logger.error(f"Failed to get project files: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/{run_id}/{format}")
async def export_results(run_id: str, format: str):
    """Export analysis results in specified format"""
    try:
        results = db_manager.get_results(run_id)
        
        if format == "json":
            return results
        elif format == "pdf":
            # Placeholder - would generate PDF
            return {"message": "PDF export not implemented yet"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """Get all configuration settings"""
    try:
        config = db_manager.get_all_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/{config_key}")
async def get_config_value(config_key: str):
    """Get specific configuration value"""
    try:
        value = db_manager.get_config(config_key)
        if value is None:
            raise HTTPException(status_code=404, detail="Configuration key not found")
        return {"key": config_key, "value": value}
    except Exception as e:
        logger.error(f"Failed to get config value: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/{config_key}")
async def set_config_value(config_key: str, request: dict):
    """Set configuration value"""
    try:
        value = request.get("value")
        config_type = request.get("type", "string")
        description = request.get("description")
        
        if value is None:
            raise HTTPException(status_code=400, detail="Value is required")
        
        db_manager.set_config(config_key, str(value), config_type, description)
        return {"success": True, "message": f"Configuration {config_key} updated"}
    except Exception as e:
        logger.error(f"Failed to set config value: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exports")
async def list_exports():
    """List all exported project data"""
    try:
        exports_dir = db_manager.get_config('project_exports_dir') or './exports'
        exports_path = Path(exports_dir)
        
        if not exports_path.exists():
            return []
        
        exports = []
        for export_dir in exports_path.iterdir():
            if export_dir.is_dir():
                metadata_file = export_dir / "export_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        metadata['export_path'] = str(export_dir)
                        exports.append(metadata)
                    except:
                        pass
        
        return exports
    except Exception as e:
        logger.error(f"Failed to list exports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filesystem/browse")
async def browse_filesystem(path: str = "/"):
    """Browse file system"""
    try:
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise HTTPException(status_code=404, detail="Path does not exist")
        
        items = []
        
        if path_obj.is_dir():
            for item in sorted(path_obj.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })
        
        return items
        
    except Exception as e:
        logger.error(f"Failed to browse filesystem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/processing/{run_id}")
async def websocket_processing(websocket: WebSocket, run_id: str):
    """WebSocket for real-time processing updates"""
    await websocket.accept()
    
    # Add to connections
    if run_id not in processing_manager.websocket_connections:
        processing_manager.websocket_connections[run_id] = []
    processing_manager.websocket_connections[run_id].append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Remove from connections
        if run_id in processing_manager.websocket_connections:
            processing_manager.websocket_connections[run_id].remove(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )