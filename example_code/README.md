# Example Code from MCP Crawl4AI RAG Project

This directory contains valuable code patterns and components from the MCP Crawl4AI RAG project that can be applied to enhance this Python debug tool.

## Files Overview with Domain Classification

### Infrastructure Layer (Adapters & External Integrations)
- **`hash_based_file_tracker.py`** (originally `process_folder_for_embeddings.py`)
  - **Domain**: Infrastructure/Adapters
  - **Purpose**: File system adapter with hash-based change detection
  - Hash-based incremental file processing system
  - Smart git repository detection
  - File change tracking with `.code_hashes.json`
  - Handles moved/renamed files efficiently
  - **Classes**: `SimpleFolderProcessor`, `SimpleCodeChunk`
  - **Key Methods**: `process_folder()`, `_load_hash_cache()`, `_detect_git_repositories()`

- **`database_utils.py`** (originally `src/utils.py`)
  - **Domain**: Infrastructure/Adapters
  - **Purpose**: Database and API service adapters
  - Supabase and OpenAI integration utilities
  - Embedding generation and storage
  - Database client setup and management
  - **Key Functions**: `get_supabase_client()`, `create_embeddings_batch()`, `create_embedding()`

- **`ast_dependency_extraction.py`**
  - **Domain**: Application/Services
  - **Purpose**: AST-based dependency analysis and relationship extraction
  - Extracts imports, function calls, method calls, class inheritance
  - Generates Neo4j Cypher queries for relationship creation
  - Tracks class usage, type annotations, and object instantiation
  - **Classes**: `DependencyExtractor` (AST NodeVisitor)
  - **Key Methods**: `visit_Import()`, `visit_Call()`, `visit_ClassDef()`, `generate_neo4j_cypher_queries()`

- **`bridge_supabase_neo4j.py`**
  - **Domain**: Infrastructure/Adapters
  - **Purpose**: Bridge adapter between vector and graph databases
  - Bridge between vector embeddings and knowledge graphs
  - Architectural metadata enrichment
  - Schema discovery and adaptation
  - **Classes**: `ArchitecturalBridge`

### Application Layer (Core Business Logic)
- **`enhanced_ast_analyzer.py`** (originally `Parse_into_knowledge_graph_repo_MK2.py`)
  - **Domain**: Application/Services
  - **Purpose**: Core AST analysis and knowledge graph service
  - Enhanced AST analysis with .pyi stub processing
  - Neo4j knowledge graph integration
  - Type validation and hallucination detection
  - **Classes**: `EnhancedNeo4jCodeAnalyzer`
  - **Key Methods**: `analyze_python_file()`, `jls_extract_def()`, `analyze_ai_generated_script()`

- **`comprehensive_hallucination_detector.py`**
  - **Domain**: Application/Services
  - **Purpose**: Orchestration service for hallucination detection
  - Multi-layered hallucination detection framework
  - Combines knowledge graph, regex, and framework analysis
  - Confidence scoring and risk assessment
  - **Classes**: `ComprehensiveResult`, main detection orchestrator

- **`hexagonal_architecture_analyzer.py`**
  - **Domain**: Application/Services
  - **Purpose**: Architecture analysis service
  - Automatic detection of hexagonal architecture patterns
  - Classification into architectural layers
  - Component relationship analysis
  - **Classes**: `ArchitecturalTag`, `HexagonalArchitectureAnalyzer`

### Domain Layer (Core Algorithms & Detection Logic)
- **`hallucination_detection_framework.py`**
  - **Domain**: Domain/Core
  - **Purpose**: Core hallucination detection algorithms
  - Core framework for AI hallucination detection
  - Extensible architecture for different detection methods
  - **Classes**: `ValidationLevel` (enum), detection framework classes
  - **Key Concepts**: Multi-layered validation, adversarial testing

- **`regex_hallucination_detector.py`**
  - **Domain**: Domain/Core
  - **Purpose**: Pattern-based detection algorithms
  - Pattern-based detection of suspicious code constructs
  - Identifies common AI generation artifacts
  - **Classes**: `SuspicionLevel` (enum), `SuspiciousPattern`, `RegexHallucinationDetector`

### Test/Debug Layer (Development Support)
- **`debug_parser.py`**
  - **Domain**: Test/Debug
  - **Purpose**: Development debugging utilities
  - AST parsing validation and testing
  - Comparison between different parsing approaches
  - Error detection and reporting
  - **Key Functions**: `debug_parsing()`, file analysis utilities

- **`debug_database.py`**
  - **Domain**: Test/Debug
  - **Purpose**: Database debugging utilities
  - Neo4j database validation utilities
  - Relationship integrity checking
  - Query testing and correction
  - **Key Functions**: `debug_database()`, connection testing

## Key Integration Opportunities

### 1. Hash-Based Change Detection
Extract the hash caching system from `hash_based_file_tracker.py` (lines 942-971) to implement incremental parsing in your debug tool. This will significantly speed up development cycles.

### 2. Enhanced Hallucination Detection
Integrate the multi-layered approach from `comprehensive_hallucination_detector.py` with your existing `ai_hallucination_detector.py` for more robust validation.

### 3. Smart Git Detection
Use the git repository detection logic from `hash_based_file_tracker.py` (lines 1176-1290) to make your tool automatically focus on project code rather than dependencies.

### 4. Architectural Analysis
Enhance your hexagonal architecture analysis by combining patterns from `hexagonal_architecture_analyzer.py` with your existing implementation.

### 5. Debug Utilities
Adopt the debug patterns from `debug_parser.py` and `debug_database.py` to improve your tool's troubleshooting capabilities.

## Domain-Based Integration Strategy

### Infrastructure Layer Integrations
**Target Location**: `backend/parser/` and new `backend/infrastructure/` directory

1. **Hash-Based Change Detection** (`hash_based_file_tracker.py`)
   - Extract hash caching system for incremental parsing
   - Implement in `backend/parser/` to speed up development cycles
   - **Integration Point**: Create `FileChangeTracker` adapter class

2. **Database Adapters** (`database_utils.py`, `bridge_supabase_neo4j.py`)
   - Enhance Neo4j integration in `backend/graph_builder/`
   - Add vector database support for semantic search
   - **Integration Point**: Extend existing `neo4j_exporter.py`

### Application Layer Integrations
**Target Location**: `backend/parser/` services and new application services

3. **Enhanced AST Analysis** (`enhanced_ast_analyzer.py`)
   - Integrate .pyi stub processing into existing parsers
   - Enhance `backend/parser/ast_visitors.py` with type validation
   - **Integration Point**: Extend `codebase_parser.py` with enhanced methods

4. **Architecture Analysis Service** (`hexagonal_architecture_analyzer.py`)
   - Merge with existing `New_Project/hexagonal_architecture_analyzer.py`
   - Create unified architecture classification service
   - **Integration Point**: New `backend/classifier/architecture_service.py`

### Domain Layer Integrations
**Target Location**: `backend/classifier/` and new domain logic modules

5. **Hallucination Detection Core** (`hallucination_detection_framework.py`, `regex_hallucination_detector.py`)
   - Extract pure detection algorithms from framework dependencies
   - Integrate with existing `ai_hallucination_detector.py`
   - **Integration Point**: Create `backend/classifier/hallucination_detection/` module

6. **Multi-layered Validation** (`comprehensive_hallucination_detector.py`)
   - Implement orchestration logic in application layer
   - Coordinate between different detection methods
   - **Integration Point**: New `backend/api/validation_service.py`

### Test/Debug Layer Integrations
**Target Location**: Enhance existing `tests/` and create debug utilities

7. **Debug Utilities** (`debug_parser.py`, `debug_database.py`)
   - Add to existing test suite and development tools
   - Create debugging endpoints in API
   - **Integration Point**: Enhance `backend/parser/test_parser.py` and add debug routes

## Usage Notes

- These files contain mature, production-tested patterns
- They demonstrate proper error handling and logging
- The hash-based system has been proven to handle large codebases efficiently
- The hallucination detection has multiple validation layers for reliability

## Next Steps

1. Review each file to understand the implementation patterns
2. Extract reusable components that align with your debug tool's architecture
3. Adapt the patterns to fit your existing codebase structure
4. Consider implementing incremental processing first for immediate performance benefits