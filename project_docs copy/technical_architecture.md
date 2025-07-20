# Technical Architecture Document

## System Overview

The Python Debugging Utility is designed as a modular system with clear separation of concerns, following the principle that "all code is analyzed equally, with intent tags enhancing (never gating) the analysis."

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   API Gateway   │    │   Analysis      │
│   (Frontend)    │◄──►│   (FastAPI)     │◄──►│   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Neo4j       │    │   AI Services   │
│   (Versioning)  │    │  (Knowledge     │    │   (Domain       │
│                 │    │   Graph)        │    │   Classification)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Chroma DB     │
                                              │   (Embeddings)  │
                                              └─────────────────┘
```

## Core Components

### 1. Analysis Engine
**Purpose**: Central orchestrator for all code analysis activities.

**Responsibilities**:
- Code parsing and AST generation
- Tool integration (astroid, mypy, pylint)
- Intent tag processing
- Result aggregation and scoring

**Key Classes**:
```python
class AnalysisEngine:
    def analyze_project(self, project_path: str) -> AnalysisResult
    def analyze_file(self, file_path: str) -> FileAnalysis
    def process_intent_tags(self, tags: List[IntentTag]) -> IntentAnalysis

class CodeParser:
    def parse_python_file(self, file_path: str) -> AST
    def extract_metadata(self, ast: AST) -> FileMetadata

class IntentProcessor:
    def extract_tags(self, file_content: str) -> List[IntentTag]
    def validate_intent_implementation(self, intent: Intent, implementation: Code) -> DriftAnalysis
```

### 2. AI Services
**Purpose**: Handles all AI-powered analysis including domain classification and architectural insights.

**Responsibilities**:
- Domain classification with confidence scoring
- Architectural pattern detection
- Intent vs implementation analysis
- Code similarity analysis

**Key Classes**:
```python
class DomainClassifier:
    def classify_code(self, code: str, context: Dict) -> Classification
    def get_confidence_score(self, classification: Classification) -> float

class ArchitecturalAnalyzer:
    def detect_patterns(self, codebase: Codebase) -> List[Pattern]
    def analyze_violations(self, intent: Intent, implementation: Code) -> List[Violation]

class EmbeddingService:
    def generate_embeddings(self, code_chunks: List[str]) -> List[Embedding]
    def find_similar_code(self, query_embedding: Embedding) -> List[SimilarCode]
```

### 3. Knowledge Graph Service
**Purpose**: Manages the Neo4j knowledge graph for relationship visualization and querying.

**Responsibilities**:
- Graph schema management
- Node and relationship creation/updates
- Complex relationship queries
- Graph visualization data preparation

**Graph Schema**:
```cypher
// Node Types
(:File {path, name, size, last_modified})
(:Function {name, signature, complexity, domain})
(:Class {name, inheritance, domain})
(:Module {name, imports, exports})
(:Intent {tag, description, scope, confidence})

// Relationship Types
(:File)-[:CONTAINS]->(:Function)
(:File)-[:CONTAINS]->(:Class)
(:Function)-[:CALLS]->(:Function)
(:Class)-[:INHERITS]->(:Class)
(:Module)-[:IMPORTS]->(:Module)
(:Intent)-[:APPLIES_TO]->(:Function|:Class|:Module)
(:Function)-[:IMPLEMENTS]->(:Intent)
```

### 4. Data Storage Layer
**Purpose**: Manages persistent storage across PostgreSQL, Neo4j, and Chroma DB.

**PostgreSQL Schema**:
```sql
-- Projects and versioning
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    version_hash VARCHAR(64),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(50)
);

CREATE TABLE file_analyses (
    id UUID PRIMARY KEY,
    analysis_run_id UUID REFERENCES analysis_runs(id),
    file_path TEXT NOT NULL,
    domain_classification JSONB,
    intent_tags JSONB,
    violations JSONB,
    metrics JSONB
);
```

### 5. API Gateway
**Purpose**: FastAPI-based REST API providing all backend functionality to the frontend.

**Key Endpoints**:
```python
# Project Management
POST /api/projects/                 # Create new project
GET /api/projects/                  # List projects
GET /api/projects/{id}/             # Get project details
DELETE /api/projects/{id}/          # Delete project

# Analysis
POST /api/projects/{id}/analyze/    # Start analysis
GET /api/projects/{id}/analysis/    # Get latest analysis
GET /api/analysis/{run_id}/         # Get specific analysis run

# Knowledge Graph
GET /api/projects/{id}/graph/       # Get graph data
GET /api/projects/{id}/graph/query/ # Execute graph query

# Intent Management
GET /api/projects/{id}/intents/     # List intent tags
POST /api/projects/{id}/intents/    # Add intent tag
PUT /api/intents/{id}/              # Update intent tag
```

### 6. Frontend (React)
**Purpose**: User interface for project management, analysis visualization, and configuration.

**Key Components**:
```typescript
// Main Application
App.tsx                    // Root component with routing
ProjectDashboard.tsx       // Project overview and management
AnalysisView.tsx          // Analysis results and visualizations

// Analysis Components
CodeAnalysisPanel.tsx     // File-by-file analysis results
GraphVisualization.tsx    // Neo4j graph visualization
IntentManager.tsx         // Intent tag management
ViolationsList.tsx        // Architectural violations display

// Configuration
ProjectSettings.tsx       // Project-specific configuration
AnalysisConfig.tsx       // Analysis tool configuration
```

## Data Flow

### Analysis Pipeline
1. **Project Selection**: User selects project through React UI
2. **Configuration**: System loads project-specific analysis configuration
3. **Code Discovery**: Analysis engine discovers all Python files
4. **Parsing**: Each file is parsed using AST and additional tools
5. **Intent Extraction**: Intent tags are extracted from comments/decorators
6. **AI Classification**: Code is classified by domain using AI services
7. **Graph Generation**: Relationships are mapped and stored in Neo4j
8. **Violation Detection**: Intent vs implementation drift is analyzed
9. **Result Storage**: All results are versioned and stored in PostgreSQL
10. **Visualization**: Results are formatted and sent to React frontend

### Real-time Updates
- WebSocket connection for long-running analysis progress
- Incremental updates to knowledge graph
- Live violation detection as code changes

## Configuration Management

### Project Configuration
```yaml
# .debug_tool_config.yaml
project:
  name: "My Python Project"
  analysis_depth: "deep"  # shallow, medium, deep
  
tools:
  enabled:
    - ast
    - astroid
    - mypy
    - pylint
  
ai:
  model: "gpt-4"
  fallback: "claude-3"
  confidence_threshold: 0.7
  
intent_tags:
  enabled: true
  syntax: "comment"  # comment, decorator, external
  validation: "strict"  # strict, lenient, disabled

graph:
  max_depth: 5
  include_external_deps: false
  
storage:
  retention_days: 90
  auto_cleanup: true
```

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/debugtool
      - NEO4J_URL=bolt://neo4j:7687
      
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=debugtool
      
  neo4j:
    image: neo4j:5.0
    ports: ["7474:7474", "7687:7687"]
    
  chroma:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
```

### Production Considerations
- Container orchestration (Kubernetes/Docker Swarm)
- Load balancing for API gateway
- Database clustering and backup strategies
- Monitoring and logging (Prometheus, Grafana, ELK stack)
- Security (API authentication, network policies)

## Security Architecture

### Authentication & Authorization
- JWT-based API authentication
- Role-based access control (Admin, Architect, Developer)
- Project-level permissions

### Data Protection
- Encryption at rest for sensitive code analysis
- Secure API key management for AI services
- Network security between components
- Audit logging for all analysis activities

## Performance Considerations

### Scalability Targets
- **Small Projects** (< 1K files): < 30 seconds analysis
- **Medium Projects** (1K-10K files): < 5 minutes analysis  
- **Large Projects** (10K+ files): < 30 minutes analysis

### Optimization Strategies
- Parallel file processing
- Incremental analysis (only changed files)
- Caching of AI classification results
- Database query optimization
- Lazy loading in frontend

## Monitoring and Observability

### Key Metrics
- Analysis completion time by project size
- AI model accuracy and confidence scores
- Knowledge graph query performance
- User engagement with violations and insights

### Health Checks
- Database connectivity
- AI service availability
- Knowledge graph responsiveness
- File system access permissions

This architecture provides a solid foundation for the Python Debugging Utility while maintaining flexibility for future enhancements and scalability requirements.