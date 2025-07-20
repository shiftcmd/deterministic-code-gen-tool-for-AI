# Python Codebase Debugging Utility

> **A comprehensive debugging and analysis utility for large Python projects that combines static analysis, AI-powered domain classification, knowledge graph construction, and architectural intent tracking.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-green.svg)](https://neo4j.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)

## 🎯 Core Philosophy

**All code is analyzed equally. Intent tags enhance, never gate.**

This tool provides comprehensive architectural analysis whether your code has intent annotations or not. When developers express architectural intent through configurable tags, the system can detect drift between design and implementation. Without tags, it provides full architectural analysis based on code structure alone.

## ✨ Key Features

### 🔍 **Universal Code Analysis**
- **AST-based Python parsing** - Deep structural analysis of any Python codebase
- **Multi-tool integration** - Combines astroid, mypy, pylint, and custom analyzers
- **Relationship extraction** - Maps imports, calls, inheritance, and dependencies
- **Architectural pattern detection** - Identifies design patterns and architectural styles

### 🧠 **AI-Powered Classification**
- **Domain classification** with confidence scoring
- **Architectural layer detection** (Core, Application, Infrastructure)
- **Pattern recognition** (Repository, Factory, Adapter, etc.)
- **Code similarity analysis** using embeddings

### 🏗️ **Intent Tracking System**
- **Optional intent tagging** - Express architectural design through comments
- **Drift detection** - Compare intended design vs actual implementation
- **Violation reporting** - Identify architectural boundary violations
- **Tag-aware analysis** - Enhanced AI prompting with architectural context

### 📊 **Knowledge Graph Visualization**
- **Interactive Neo4j graphs** - Explore code relationships visually
- **Multi-dimensional filtering** - By domain, layer, pattern, or custom criteria
- **Architectural violation highlighting** - Visual identification of design issues
- **Historical analysis** - Track architectural evolution over time

### 🔄 **Version Management**
- **PostgreSQL-backed versioning** - Track analysis results over time
- **Graph snapshots** - Preserve knowledge graphs for comparison
- **Change tracking** - Monitor architectural drift across versions
- **Rollback capabilities** - Compare current state to any previous version

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ 
- Node.js 18+ (for React frontend)
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd python_debug_tool
   ```

2. **Set up the development environment**
   ```bash
   make setup
   ```
   
   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server**
   ```bash
   make serve
   # or
   ./scripts/dev.py serve
   ```

5. **Run tests**
   ```bash
   make test
   # or
   ./scripts/dev.py test
   ```

## 🛠️ Development Commands

### Using Make (Recommended)

```bash
# Setup and installation
make setup          # Initial project setup
make install        # Install/update dependencies

# Development
make serve          # Start development server
make test           # Run tests
make test-cov       # Run tests with coverage

# Code quality
make format         # Format code (black + isort)
make lint           # Run linting (flake8 + mypy)
make check          # Run all checks (format + lint + test)

# Utilities
make clean          # Clean up generated files
make status         # Show project status
make help           # Show available commands
```

### Using Development Script

```bash
# All make commands are also available via the dev script:
./scripts/dev.py serve
./scripts/dev.py test
./scripts/dev.py format
./scripts/dev.py lint
./scripts/dev.py check
./scripts/dev.py clean
```

## 📁 Project Structure

```
python_debug_tool/
├── backend/                 # Python backend application
│   ├── api/                # FastAPI routes and endpoints
│   ├── classifier/         # AI-powered domain classification
│   ├── graph_builder/      # Neo4j knowledge graph construction
│   ├── parser/             # Python AST parsing and analysis
│   ├── version_manager/    # PostgreSQL version tracking
│   ├── config.py          # Configuration management
│   └── main.py            # FastAPI application entry point
├── frontend/               # React frontend application
├── tests/                  # Test suite
├── scripts/                # Development utilities
│   └── dev.py             # Development script
├── docs/                   # Documentation
├── project_docs/           # Project planning and analysis
├── .taskmaster/           # Task management (taskmaster tool)
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Project configuration
├── Makefile               # Development commands
└── README.md              # This file
```

## 🔧 Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

### Application Settings
- `ENVIRONMENT`: development/staging/production
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `NEO4J_URI`: Neo4j database URI
- `REDIS_URL`: Redis connection string

### AI Services (Optional)
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `PERPLEXITY_API_KEY`: Perplexity API key for research capabilities
- `GOOGLE_API_KEY`: Google API key for Gemini models
- `MISTRAL_API_KEY`: Mistral API key for Mistral models

> **Note**: AI services are optional. The tool can perform structural analysis without AI classification.

## 🧪 Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
./scripts/dev.py test tests/test_main.py

# Run tests with specific pytest options
./scripts/dev.py test -- -v -k "test_specific_function"
```

## 🎨 Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

```bash
# Format code
make format

# Run linting
make lint

# Run all quality checks
make check
```

## 🏗️ Architecture

### Core Components

1. **AST Parser Engine**: Analyzes Python code structure using AST and astroid
2. **Domain Classification System**: AI-powered code categorization
3. **Knowledge Graph Builder**: Creates Neo4j graphs of code relationships
4. **Intent Tagging System**: Tracks architectural intent vs implementation
5. **Version Manager**: PostgreSQL-based analysis history tracking
6. **React Frontend**: User interface for visualization and management

### Technology Stack

**Backend:**
- FastAPI (API framework)
- Python 3.11+ (runtime)
- PostgreSQL (version tracking)
- Neo4j (knowledge graph)
- Redis (caching)
- Chroma DB (embeddings)

**Frontend:**
- React 18+ (UI framework)
- TypeScript (type safety)
- Node.js (runtime)

**AI/ML:**
- OpenAI GPT models
- Anthropic Claude
- Perplexity (research)

## 📊 Current Status & Roadmap

### ✅ **Completed (Phase 1-2)** 
- [x] **Core Infrastructure**: Project structure, development environment, CI/CD pipeline
- [x] **AST Parsing Engine**: Python file parsing with AST, astroid, and custom analyzers
- [x] **Basic Analysis**: Structural element extraction and relationship mapping
- [x] **Neo4j Integration**: Knowledge graph schema and basic graph operations
- [x] **PostgreSQL Setup**: Version management and analysis result storage
- [x] **Performance Optimization**: Hash-based caching, parallel processing, incremental parsing
- [x] **Testing Framework**: Comprehensive test suite with performance tests

### 🚧 **In Progress (Phase 3)** - Target: Q1 2025
- [ ] **React Frontend Development** (60% complete)
  - [x] Project structure and component architecture
  - [ ] Graph visualization components
  - [ ] Analysis dashboard and results display
  - [ ] Real-time progress tracking
- [ ] **Enhanced AI Integration** (40% complete)
  - [x] Multi-model AI service abstraction
  - [ ] Domain classification with confidence scoring
  - [ ] Architectural pattern detection
  - [ ] Result validation and consensus mechanisms
- [ ] **Advanced Parser Features** (70% complete)
  - [x] Multi-tool integration (astroid, mypy, pylint)
  - [x] Relationship extraction and dependency analysis
  - [ ] Code complexity metrics and quality assessment
  - [ ] Security vulnerability detection integration

### 📅 **Planned Features**

#### **Phase 4: Intent Tracking System** (Q2 2025)
- [ ] **Intent Tagging Infrastructure**
  - [ ] Configurable tag syntax and parsing
  - [ ] Tag validation and storage system
  - [ ] Intent tag management UI
  - [ ] Versioning and history tracking
- [ ] **Drift Detection Engine**
  - [ ] Intent vs implementation comparison algorithms
  - [ ] Architectural violation detection and scoring
  - [ ] Drift visualization and reporting
  - [ ] Tag-aware AI analysis enhancement

#### **Phase 5: Advanced Analysis** (Q3 2025)
- [ ] **Architectural Analysis**
  - [ ] Hexagonal architecture pattern detection
  - [ ] Layer boundary violation identification
  - [ ] Dependency cycle detection and resolution
  - [ ] Design pattern recognition and validation
- [ ] **Code Quality Assessment**
  - [ ] Technical debt trend analysis
  - [ ] Code similarity and duplication detection
  - [ ] Performance hotspot identification
  - [ ] Maintainability scoring and recommendations

#### **Phase 6: Semantic Search & Embeddings** (Q4 2025)
- [ ] **Vector Database Integration**
  - [ ] Chroma DB setup and code embedding generation
  - [ ] Semantic code search capabilities
  - [ ] Similarity-based code recommendations
  - [ ] Duplicate code detection using embeddings
- [ ] **MCP Server Implementation**
  - [ ] Model Context Protocol server for external tool integration
  - [ ] Semantic search API endpoints
  - [ ] Natural language querying of codebase
  - [ ] Advanced architectural insights through vector analysis

### 🎯 **Success Metrics**
- **Analysis Performance**: Parse 100K+ lines of code in under 5 minutes
- **Classification Accuracy**: >85% accuracy in AI-powered domain classification
- **User Adoption**: Intent tagging used in 40%+ of analyzed projects
- **Architectural Compliance**: <10% drift rate in tagged codebases
- **Developer Productivity**: 30%+ reduction in code review time for architectural issues

### 📈 **Long-term Vision**
- **Multi-language Support**: Extend analysis to JavaScript, Java, C#
- **IDE Integration**: VS Code and PyCharm plugins for real-time analysis
- **CI/CD Integration**: Automated architectural compliance checking in pipelines
- **Collaborative Features**: Team-based architectural decision tracking
- **Machine Learning**: Continuous improvement of pattern recognition through usage data

## 🔄 CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

### Workflows

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs on Python 3.11 and 3.12
  - Executes pre-commit hooks
  - Runs test suite with coverage reporting
  - Uploads coverage to Codecov
  - Performs security checks with Bandit and Safety
  - Builds the package

- **Frontend Pipeline** (`.github/workflows/frontend.yml`):
  - Runs when frontend files are modified
  - Tests and builds the React frontend
  - Uses Node.js 18 with npm caching

### Quality Gates

All pull requests must pass:
- ✅ Code formatting (Black, isort)
- ✅ Linting (flake8)
- ✅ Type checking (mypy)
- ✅ Security checks (Bandit, Safety)
- ✅ Test coverage requirements
- ✅ Pre-commit hooks

## 💡 Use Cases & Examples

### 🔍 **Legacy Code Analysis**
```python
# Analyze an undocumented codebase
from debugtool import AnalysisEngine

engine = AnalysisEngine()
results = engine.analyze_project("/path/to/legacy/codebase")

# Get architectural insights without any prior knowledge
architecture = results.get_architecture_summary()
violations = results.get_potential_violations()
```

### 🤖 **AI Code Review**
```python
# Validate AI-generated code against architectural patterns
# @intent: core:entity:immutable
# @business-rule: User email must be unique
class User:
    def __init__(self, email: str):
        self._email = email
    
    def change_email(self, new_email: str):  # Drift detected!
        self._email = new_email  # Violates immutable intent
```

### 🏛️ **Architecture Compliance**
```python
# Express architectural intent through tags
# @intent: infrastructure:adapter:repository
# @implements: UserRepository
# @depends-on: application:port
class PostgresUserRepository:
    def __init__(self, db_connection):
        self.db = db_connection  # ✅ Correctly in infrastructure layer
    
    def save(self, user):
        # Implementation follows intended pattern
        pass
```

### 📈 **Technical Debt Tracking**
- Track architectural drift over time
- Identify components that violate intended design
- Measure compliance with architectural patterns
- Generate reports on code quality trends

## 🛠️ Example Analysis Output

```json
{
  "project_summary": {
    "total_files": 234,
    "analysis_time": "2.3 minutes",
    "confidence_score": 0.87
  },
  "architectural_layers": {
    "core": {"files": 45, "violations": 2},
    "application": {"files": 67, "violations": 8},
    "infrastructure": {"files": 89, "violations": 3}
  },
  "violations": [
    {
      "type": "layer_violation",
      "file": "core/entities/user.py",
      "issue": "Core entity imports infrastructure adapter",
      "severity": "high"
    }
  ],
  "recommendations": [
    "Consider extracting database logic to infrastructure layer",
    "Add intent tags to clarify architectural boundaries"
  ]
}
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Check the documentation in the `docs/` directory
- Review project planning in `project_docs/`
- Open an issue for bugs or feature requests

---

**Happy Debugging! 🐛🔍**
