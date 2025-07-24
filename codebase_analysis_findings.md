# Python Debug Tool Codebase Analysis

## Project Overview

The **Python Debug Tool** is a comprehensive debugging and analysis utility for large Python projects that combines static analysis, AI-powered domain classification, knowledge graph construction, and architectural intent tracking. The project follows the core philosophy: *"All code is analyzed equally. Intent tags enhance, never gate."*

## Architecture Overview

### Technology Stack

**Backend:**
- **FastAPI** (API framework) with Python 3.11+
- **PostgreSQL** (version tracking and metadata storage)  
- **Neo4j** (knowledge graph relationships)
- **Redis** (caching)
- **Chroma DB** (embeddings for semantic search)
- **Multiple Python analysis tools**: astroid, mypy, pylint, pyflakes

**Frontend:**
- **React 19** with JSX (not TypeScript)
- **Vite** as build tool
- **Ant Design (antd)** for UI components
- **Axios** for API communication

**AI/ML Integration:**
- **OpenAI** (GPT models)
- **Anthropic** (Claude models) 
- **Perplexity** (research capabilities)
- **Chroma DB** (local embeddings)

## Project Structure

```
python_debug_tool/
├── backend/                    # Python FastAPI backend
│   ├── api/                   # API routes (files, analysis, health, runs, ide)
│   ├── classifier/            # AI-powered domain classification
│   ├── graph_builder/         # Neo4j knowledge graph construction
│   ├── parser/                # Python AST parsing and analysis
│   │   ├── dev/              # Development version of parser
│   │   ├── prod/             # Production refactored parser
│   │   ├── plugins/          # Parser plugins (AST, astroid, inspect4py)
│   │   └── exporters/        # Data export utilities
│   ├── version_manager/       # PostgreSQL version tracking
│   ├── config.py             # Configuration management
│   └── main.py              # FastAPI application entry
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── pages/            # Route components (Dashboard, FileExplorer, etc.)
│   │   ├── components/       # Reusable UI components
│   │   ├── services/         # API client
│   │   ├── context/          # React context providers
│   │   └── hooks/            # Custom React hooks
├── tests/                     # Test suite with performance tests
├── scripts/                   # Development utilities
├── project_docs/             # Extensive project documentation
├── example_code/             # Integration examples and patterns
└── tools/                    # CLI tools and agents
```

## Key Features & Components

### 1. Universal Code Analysis Engine
- **AST-based parsing** using multiple tools (astroid, mypy, pylint)
- **Multi-tool integration** with plugin architecture
- **Relationship extraction** (imports, calls, inheritance, dependencies)
- **Performance optimization** with hash-based caching and parallel processing

### 2. Knowledge Graph System (Neo4j)
- **Interactive graph visualization** for code relationships
- **Multi-dimensional filtering** by domain, layer, pattern
- **Architectural violation highlighting**
- **Historical analysis** capabilities

### 3. AI-Powered Classification
- **Domain classification** with confidence scoring
- **Architectural layer detection** (Core, Application, Infrastructure)
- **Pattern recognition** (Repository, Factory, Adapter, etc.)
- **Code similarity analysis** using embeddings

### 4. Intent Tracking System (Optional)
- **Configurable intent tagging** through comments
- **Drift detection** between intended design vs implementation
- **Violation reporting** for architectural boundaries
- **Tag-aware analysis** enhancement

## Development Workflow

### Development Commands (Make-based)
```bash
make setup          # Initial project setup with venv
make serve          # Start development server (port 8080)
make test           # Run test suite
make test-cov       # Run tests with coverage
make format         # Code formatting (black + isort)
make lint           # Linting (flake8 + mypy)  
make check          # All quality checks
make clean          # Clean generated files
```

### Alternative: Development Script
```bash
./scripts/dev.py serve    # All make commands available
./scripts/dev.py test
./scripts/dev.py format
```

## Current Implementation Status

### ✅ **Phase 1-2 Completed**
- Core infrastructure and project setup
- AST parsing engine with multiple tool integration
- Basic analysis capabilities
- Neo4j knowledge graph integration
- PostgreSQL version management
- Performance optimizations (hash-based caching, parallel processing)
- Comprehensive test suite

### 🚧 **Phase 3 In Progress** 
- **React Frontend Development** (60% complete)
  - Basic routing and component structure
  - API integration layer
  - Missing: Graph visualization, dashboard completion
- **Enhanced AI Integration** (40% complete)
  - Multi-model service abstraction
  - Missing: Domain classification, pattern detection
- **Advanced Parser Features** (70% complete)
  - Multi-tool integration complete
  - Missing: Complexity metrics, security integration

### 📅 **Planned Features**
- **Phase 4**: Intent tracking system with drift detection
- **Phase 5**: Advanced architectural analysis
- **Phase 6**: Semantic search and embeddings integration

## API Architecture

**Current Endpoints:**
- `/health` - Health checks
- `/api/files/*` - File system operations
- `/api/analysis/*` - Code analysis operations  
- `/api/runs/*` - Analysis run management
- `/api/ide/*` - IDE integration features

**Configuration Management:**
- Environment-based settings with Pydantic
- Database connections (PostgreSQL, Neo4j, Redis)
- AI service configurations (optional)
- CORS enabled for frontend integration

## Testing & Quality

### Testing Framework
- **pytest** with asyncio support
- **Coverage reporting** with pytest-cov
- **Performance tests** in dedicated directory
- **Integration tests** for system components

### Code Quality Tools
- **Black** (formatting, line length 88)
- **isort** (import sorting)
- **flake8** (linting)
- **mypy** (type checking, strict configuration)
- **pre-commit hooks** (not currently configured)

## Development Environment

### Database Requirements
- **PostgreSQL 15+** (version tracking, metadata)
- **Neo4j 5.x** (knowledge graph)
- **Redis 5+** (caching)
- **Chroma DB** (local embeddings)

### Optional AI Services
- OpenAI API key (GPT models)
- Anthropic API key (Claude models)
- Perplexity API key (research capabilities)
- Google, Mistral, etc. (additional models)

## Key Patterns & Conventions

### Backend Patterns
- **Clean API architecture** - routes delegate to service layer
- **Configuration management** with Pydantic settings
- **Plugin-based parser system** for extensibility
- **Service layer separation** from business logic
- **Async/await** patterns throughout FastAPI

### Frontend Patterns  
- **Component-based architecture** with reusable components
- **Context providers** for state management
- **Custom hooks** for API interactions
- **Page-based routing** structure
- **Ant Design** for consistent UI components

### Data Flow
1. **File Analysis**: AST parsing → Multiple tool analysis → Relationship extraction
2. **Knowledge Graph**: Parsed data → Neo4j graph creation → Relationship queries
3. **AI Classification**: Code elements → AI analysis → Domain/pattern classification
4. **Version Management**: Analysis results → PostgreSQL storage → Historical tracking

## Integration Points

### MCP (Model Context Protocol) Integration
- Documented integration patterns in `example_code/`
- PostgreSQL + Chroma + Neo4j architecture  
- Replacement guidance for Supabase → PostgreSQL migrations
- Reference implementations for component integration

### Task Management Integration
- **TaskMaster CLI** integration documented in existing `CLAUDE.md`
- Project initialization and PRD parsing capabilities
- Task tracking and development workflow integration

## Notable Considerations

### Strengths
- **Comprehensive architecture** with clear separation of concerns
- **Multiple analysis tools** integration for robust parsing
- **Performance optimizations** built-in from early stages
- **Extensive documentation** and project planning
- **Flexible AI integration** with multiple provider support

### Areas for Enhancement
- **Frontend completion** - graph visualization and dashboard
- **AI classification** - domain classification implementation
- **Intent tracking** - full drift detection system
- **CI/CD pipeline** - GitHub Actions not currently configured
- **Documentation** - API documentation generation

## Conclusion

This codebase represents a well-architected, ambitious project for Python code analysis with solid foundations and clear roadmap for completion. The modular design and comprehensive documentation make it well-suited for collaborative development.