# Database and Storage Configuration Guide

## 📂 Database Location and Structure

### SQLite Database
- **Location**: `/home/amo/coding_projects/python_debug_tool/framework_runs.db`
- **Purpose**: Stores all analysis runs, results, configuration, and processing logs
- **Auto-created**: When the backend server starts

### Database Schema

#### 1. `runs` Table
Stores analysis run metadata:
```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,              -- Unique run identifier (UUID)
    project_path TEXT NOT NULL,       -- Path to analyzed project
    project_name TEXT,                -- Extracted project name
    status TEXT NOT NULL,             -- running, completed, failed, stopped
    started_at TIMESTAMP,             -- When analysis started
    completed_at TIMESTAMP,           -- When analysis finished
    file_count INTEGER,               -- Number of files analyzed
    selected_files TEXT,              -- JSON array of selected files
    error TEXT,                       -- Error message if failed
    neo4j_data_path TEXT,            -- Path to exported Neo4j data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `run_results` Table
Stores analysis results as JSON:
```sql
CREATE TABLE run_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,             -- Links to runs.id
    result_type TEXT NOT NULL,        -- main_analysis, actionable_report, etc.
    result_data TEXT NOT NULL,        -- JSON data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs (id)
);
```

#### 3. `processing_logs` Table
Stores real-time processing logs:
```sql
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,             -- Links to runs.id
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,              -- INFO, DEBUG, ERROR, WARNING
    message TEXT NOT NULL,            -- Log message
    FOREIGN KEY (run_id) REFERENCES runs (id)
);
```

#### 4. `framework_config` Table
Stores configuration settings:
```sql
CREATE TABLE framework_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,  -- Configuration key
    config_value TEXT NOT NULL,       -- Configuration value
    config_type TEXT DEFAULT 'string', -- string, integer, boolean, float
    description TEXT,                 -- Human-readable description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ⚙️ Default Configuration

The system automatically creates these default configuration values:

| Key | Value | Type | Description |
|-----|-------|------|-------------|
| `neo4j_host` | `localhost` | string | Neo4j database host |
| `neo4j_port` | `7687` | integer | Neo4j database port |
| `neo4j_database` | `neo4j` | string | Neo4j database name |
| `neo4j_username` | `neo4j` | string | Neo4j username |
| `neo4j_data_dir` | `/var/lib/neo4j/data` | string | Neo4j data directory |
| `project_exports_dir` | `./exports` | string | Directory for exported project data |
| `max_file_size_mb` | `10` | integer | Maximum file size for analysis (MB) |
| `enable_hallucination_detection` | `true` | boolean | Enable AI hallucination detection |
| `enable_neo4j_export` | `true` | boolean | Enable Neo4j knowledge graph export |
| `processing_timeout_minutes` | `30` | integer | Processing timeout in minutes |

## 🗂️ Neo4j Data Export Structure

After each successful analysis, the system automatically:

1. **Copies Neo4j data** from the configured data directory
2. **Creates project-specific folder** named: `{project_name}_{run_id_first_8_chars}`
3. **Exports to**: `./exports/{project_name}_{run_id}/`

### Export Directory Structure
```
exports/
└── my_project_abc12345/          # Project + Run ID
    ├── neo4j_data/               # Complete Neo4j database copy
    │   ├── databases/
    │   ├── dbms/
    │   └── transactions/
    ├── export_metadata.json      # Export metadata
    ├── full_framework_analysis_abc12345.json    # Analysis results
    └── actionable_framework_report_abc12345.json # Recommendations
```

### Export Metadata File
```json
{
  "run_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "project_name": "my_project",
  "project_path": "/path/to/analyzed/project",
  "neo4j_data_path": "./exports/my_project_abc12345/neo4j_data",
  "exported_at": "2024-07-21T01:52:30.123456",
  "file_count": 42,
  "started_at": "2024-07-21T01:50:00.000000",
  "completed_at": "2024-07-21T01:52:30.000000"
}
```

## 🔧 Configuration Management

### View Configuration
```bash
# Get all configuration
curl http://localhost:8080/api/config

# Get specific configuration
curl http://localhost:8080/api/config/neo4j_host
```

### Update Configuration
```bash
# Set Neo4j data directory
curl -X POST http://localhost:8080/api/config/neo4j_data_dir \
  -H "Content-Type: application/json" \
  -d '{"value": "/custom/neo4j/data", "type": "string", "description": "Custom Neo4j data directory"}'

# Set project exports directory
curl -X POST http://localhost:8080/api/config/project_exports_dir \
  -H "Content-Type: application/json" \
  -d '{"value": "/path/to/exports", "type": "string", "description": "Custom exports directory"}'
```

### Database Inspection
```bash
# Using Python (sqlite3 not available)
python -c "
import sqlite3
conn = sqlite3.connect('framework_runs.db')

# View all runs
cursor = conn.execute('SELECT id, project_name, status, started_at FROM runs')
for row in cursor.fetchall():
    print(f'Run: {row[0][:8]} | Project: {row[1]} | Status: {row[2]} | Started: {row[3]}')

# View configuration
cursor = conn.execute('SELECT config_key, config_value FROM framework_config ORDER BY config_key')
for row in cursor.fetchall():
    print(f'Config: {row[0]} = {row[1]}')

conn.close()
"
```

## 📊 API Endpoints for Data Management

### Configuration Endpoints
- `GET /api/config` - Get all configuration
- `GET /api/config/{key}` - Get specific configuration value  
- `POST /api/config/{key}` - Set configuration value

### Runs Management
- `GET /api/runs` - List all analysis runs
- `GET /api/runs/{run_id}` - Get specific run details
- `GET /api/runs/{run_id}/dashboard` - Get run analysis results
- `DELETE /api/runs/{run_id}` - Delete run and associated data

### Exports Management
- `GET /api/exports` - List all exported project data
- `GET /api/export/{run_id}/{format}` - Export run results (json/pdf)

## 🚀 Automatic Neo4j Data Processing

The system automatically handles Neo4j data export through this workflow:

1. **Analysis Completion**: When framework analysis finishes successfully
2. **Data Discovery**: Locates Neo4j data directory from configuration
3. **Project Naming**: Extracts project name from the analyzed path
4. **Directory Creation**: Creates `./exports/{project}_{run_id}/` directory
5. **Data Copy**: Copies entire Neo4j data directory to export location
6. **Metadata Creation**: Generates export metadata with run information
7. **Database Update**: Updates run record with Neo4j data path
8. **Results Copy**: Copies analysis JSON files to export directory

## 🔍 Troubleshooting

### Database Issues
- **Database locked**: Stop backend server before manual inspection
- **Missing tables**: Backend auto-creates tables on startup
- **Permission errors**: Ensure write permissions in project directory

### Neo4j Export Issues
- **Data not copied**: Check `neo4j_data_dir` configuration points to valid directory
- **Permission denied**: Ensure read access to Neo4j data directory
- **Export directory**: Configure `project_exports_dir` to writable location

### Configuration Issues
- **Default values**: Configuration auto-populates with defaults on first run
- **Type conversion**: Boolean values: `true`/`false`, integers as strings: `"123"`
- **Reset config**: Delete `framework_runs.db` to reset to defaults

## 📁 File Locations Summary

| Item | Default Location |
|------|------------------|
| **SQLite Database** | `./framework_runs.db` |
| **Neo4j Source Data** | `/var/lib/neo4j/data` |
| **Exports Directory** | `./exports/` |
| **Project Exports** | `./exports/{project}_{run_id}/` |
| **Analysis Results** | `./full_framework_analysis_{run_id}.json` |
| **Actionable Reports** | `./actionable_framework_report_{run_id}.json` |

## 🔐 Security Considerations

- **Database**: Contains project paths and analysis data - protect access
- **Neo4j Data**: May contain sensitive project information in graph
- **Exports**: Automatically created copies contain full project analysis
- **Configuration**: Neo4j credentials stored in database - use secure values
- **File Permissions**: Ensure appropriate read/write permissions for service account

The system provides comprehensive data management with automatic Neo4j export, persistent configuration storage, and complete analysis tracking through the SQLite database.