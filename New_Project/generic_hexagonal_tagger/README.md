# Generic Hexagonal Architecture Tagging System

A comprehensive tagging system for analyzing and categorizing code components in hexagonal architecture projects.

## Features

- **AST-based Code Analysis**: Static analysis of Python source code using Abstract Syntax Trees
- **Hexagonal Architecture Support**: Built-in understanding of hexagonal architecture patterns
- **Comprehensive Tagging**: 26 predefined tags across multiple categories (Node, Layer, Role, Technical, Quality, Functional, File, Module, Relationship)
- **AI-Ready**: Placeholder for AI-assisted tagging integration
- **Neo4j Integration**: Ready for graph database persistence
- **CLI Interface**: User-friendly command-line interface with multiple output formats
- **Extensible Design**: Plugin system for custom analyzers and taggers

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

### Setup

1. Navigate to the project directory:
```bash
cd generic_hexagonal_tagger
```

2. Install dependencies:
```bash
poetry install
```

3. Configure environment variables:
```bash
# The .env file is already configured with defaults
# Edit .env to customize your configuration
```

## Usage

### Command Line Interface

The system provides a comprehensive CLI for analyzing codebases:

```bash
# Analyze a single file
python main.py analyze-file path/to/file.py --format summary

# Analyze a codebase
python main.py analyze path/to/codebase --recursive --format table

# List available tags
python main.py list-tags --category technical

# Show configuration
python main.py config-info
```

### Output Formats

- **summary**: Human-readable summary with key metrics
- **table**: Structured table view of components
- **json**: Machine-readable JSON output

### Example Usage

```bash
# Analyze the core domain files
python main.py analyze-file core/domain/tag.py --format summary

# Analyze entire core directory
python main.py analyze core --recursive --format table --include-metrics

# Save results to file
python main.py analyze core --format json --output results.json

# List all available tags
python main.py list-tags
```

### Example Output

```
📄 File: tag.py
📊 Components: 35
📁 Lines of Code: 276
🔗 Relationships: 38
🏷️  Tags: 2

Components Found:
  • class: TagCategory [Class]
  • class: TagType [Class]
  • class: Tag [Class]
  • method: validate_name [Method, Sync]
  • method: validate_confidence [Method, Sync]
```

## Architecture

The system follows hexagonal architecture principles:

```
generic_hexagonal_tagger/
├── core/                    # Domain layer
│   └── domain/             # Domain models and business logic
├── application/            # Application services
│   └── services/          # Use cases and orchestration
├── infrastructure/         # External adapters
│   └── adapters/          # Database, file system, etc.
├── interfaces/            # User interfaces
│   └── cli.py            # Command-line interface
├── config/               # Configuration management
└── main.py              # CLI entry point
```

## Configuration

The system uses environment variables for configuration (see `.env` file):

```env
# Project Settings
PROJECT_NAME="Generic Hexagonal Tagger"
VERSION="0.1.0"
DEBUG=false

# Logging
LOGGING_LEVEL=INFO
LOGGING_FILE_ENABLED=true
LOGGING_FILE_PATH=logs/tagging_system.log

# Neo4j (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# AI Services (optional)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Analysis
ANALYSIS_ENABLE_AI_TAGGING=false
ANALYSIS_ENABLE_STATIC_ANALYSIS=true
ANALYSIS_ENABLE_VALIDATION=true

# Caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

## Testing

The system has been tested and verified to work correctly:

```bash
# Test file analysis
python main.py analyze-file core/domain/tag.py --format summary

# Test directory analysis
python main.py analyze core/domain --format table

# Test tag listing
python main.py list-tags --category layer

# Test configuration display
python main.py config-info
```

## Development

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run flake8 .

# Type checking
poetry run mypy .
# Linting
poetry run flake8 .
```

## Extending the System

### Adding New Tags

```python
from generic_hexagonal_tagger.core.domain.tag import Tag, TagCategory, get_tag_registry

# Create a new tag
new_tag = Tag(
    name="CustomPattern",
    category=TagCategory.PATTERN,
    description="Custom design pattern"
)

# Register the tag
registry = get_tag_registry()
registry.register_tag(new_tag)
```

### Adding New Analyzers

Implement the analyzer interface and register it as a plugin:

```python
from generic_hexagonal_tagger.infrastructure.adapters.ast_analyzer import StaticCodeAnalyzer

class CustomAnalyzer(StaticCodeAnalyzer):
    def analyze_file(self, file_path: str):
        # Custom analysis logic
        pass
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Roadmap

- [ ] AI-assisted semantic tagging integration
- [ ] Neo4j graph database integration
- [ ] Support for additional programming languages
- [ ] Web-based dashboard
- [ ] Plugin marketplace
- [ ] Advanced architectural pattern detection
