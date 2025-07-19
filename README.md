# Python Debug Tool

A comprehensive debugging and analysis utility for large Python projects that combines static analysis, AI-powered domain classification, knowledge graph construction, and version control to detect architectural violations, AI hallucinations, and logical fallacies in codebases.

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

### AI Services
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `PERPLEXITY_API_KEY`: Perplexity API key (for research)

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

## 📊 Development Status

This project is currently in active development. See the `.taskmaster/` directory for detailed task tracking and project management.

### Current Phase: Infrastructure Setup
- ✅ Project structure and environment
- ✅ Dependency management
- ✅ Development tooling
- ✅ Pre-commit hooks
- ✅ CI/CD pipeline

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
