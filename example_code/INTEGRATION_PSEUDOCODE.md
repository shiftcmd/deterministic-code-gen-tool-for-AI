# Integration Pseudocode for MCP Components

This document outlines the pseudocode for integrating MCP Crawl4AI RAG components into the existing Python debug tool architecture.

## 1. Hash-Based File Change Detection

### New File: `backend/infrastructure/file_change_tracker.py`

```pseudocode
// Extract core hash functionality from hash_based_file_tracker.py
class FileChangeTracker:
    def __init__(cache_path):
        self.cache_path = cache_path or ".debug_tool_cache.json"
        self.hash_cache = load_cache_or_create_empty()
    
    def detect_changes(project_path):
        current_files = scan_python_files(project_path)
        changes = {
            'new': [],
            'modified': [],
            'deleted': [],
            'moved': []
        }
        
        for file_path in current_files:
            current_hash = calculate_sha256(file_path)
            cached_info = self.hash_cache.get(file_path)
            
            if not cached_info:
                changes['new'].append(file_path)
            elif cached_info['hash'] != current_hash:
                changes['modified'].append(file_path)
        
        // Detect deleted files
        for cached_file in self.hash_cache:
            if cached_file not in current_files:
                changes['deleted'].append(cached_file)
        
        // Detect moved files using hash_to_paths mapping
        changes['moved'] = detect_moved_files_by_hash()
        
        return changes
    
    def update_cache(file_path, new_hash):
        self.hash_cache[file_path] = {
            'hash': new_hash,
            'last_modified': current_timestamp(),
            'status': 'active'
        }
        save_cache_to_disk()
```

### Modify: `backend/parser/codebase_parser.py`

```pseudocode
// Add incremental parsing capability
class CodebaseParser:
    def __init__():
        self.file_tracker = FileChangeTracker()
        // ... existing init
    
    def parse_codebase_incremental(project_path):
        changes = self.file_tracker.detect_changes(project_path)
        
        // Only parse changed files
        for file_path in changes['new'] + changes['modified']:
            parsed_data = self.parse_file(file_path)
            self.update_graph(parsed_data)
            self.file_tracker.update_cache(file_path, calculate_hash(file_path))
        
        // Remove deleted files from graph
        for file_path in changes['deleted']:
            self.remove_from_graph(file_path)
            self.file_tracker.mark_deleted(file_path)
        
        // Update moved files without re-parsing
        for old_path, new_path in changes['moved']:
            self.update_file_path_in_graph(old_path, new_path)
            self.file_tracker.update_path(old_path, new_path)
```

## 2. Enhanced AST Analysis with Stub Processing

### Modify: `backend/parser/ast_visitors.py`

```pseudocode
// Enhance existing AST visitor with .pyi processing
class EnhancedASTVisitor(ast.NodeVisitor):
    def __init__():
        // ... existing init
        self.stub_processor = StubFileProcessor()
        self.type_validator = TypeValidator()
    
    def visit_FunctionDef(node):
        // ... existing function processing
        
        // Add stub validation
        if self.is_stub_file:
            stub_info = self.extract_stub_signature(node)
            return create_stub_function_node(stub_info)
        else:
            impl_info = self.extract_implementation_info(node)
            // Validate against stub if exists
            validation_result = self.type_validator.validate_against_stub(impl_info)
            return create_enhanced_function_node(impl_info, validation_result)
    
    def visit_ClassDef(node):
        // ... existing class processing
        
        // Add type validation relationships
        if not self.is_stub_file:
            type_hints = self.extract_type_hints(node)
            validation_data = self.validate_type_consistency(type_hints)
            return create_validated_class_node(node, validation_data)
```

### New File: `backend/parser/stub_processor.py`

```pseudocode
// Extract from enhanced_ast_analyzer.py
class StubFileProcessor:
    def process_stub_file(stub_path):
        tree = ast.parse(read_file(stub_path))
        stub_definitions = {
            'functions': [],
            'classes': [],
            'constants': [],
            'type_aliases': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stub_definitions['functions'].append(extract_stub_function(node))
            elif isinstance(node, ast.ClassDef):
                stub_definitions['classes'].append(extract_stub_class(node))
        
        return stub_definitions
    
    def create_validation_relationships(stub_data, implementation_data):
        relationships = []
        
        for stub_func in stub_data['functions']:
            impl_func = find_matching_implementation(stub_func, implementation_data)
            if impl_func:
                validation = validate_signature_match(stub_func, impl_func)
                relationships.append(create_validation_relationship(stub_func, impl_func, validation))
        
        return relationships
```

## 3. Multi-Layered Hallucination Detection

### New Directory: `backend/classifier/hallucination_detection/`

### New File: `backend/classifier/hallucination_detection/core_detector.py`

```pseudocode
// Extract pure algorithms from hallucination_detection_framework.py
// Integrate with existing PostgreSQL and Chroma infrastructure
class CoreHallucinationDetector:
    def __init__(postgres_client, chroma_client):
        self.postgres_client = postgres_client  // Use existing PostgreSQL connection
        self.chroma_client = chroma_client      // Use existing Chroma vector store
        self.validation_layers = [
            SyntaxValidator(),
            StaticAnalysisValidator(),
            KnowledgeGraphValidator(self.postgres_client),  // Use PostgreSQL for graph data
            PatternValidator(),
            SemanticValidator(self.chroma_client)           // Use Chroma for semantic validation
        ]
    
    def detect_hallucinations(code_snippet, context):
        results = []
        
        for validator in self.validation_layers:
            validation_result = validator.validate(code_snippet, context)
            results.append(validation_result)
        
        // Store validation results in PostgreSQL for tracking
        self.store_validation_result(code_snippet, results)
        
        combined_confidence = calculate_weighted_confidence(results)
        risk_level = determine_risk_level(combined_confidence)
        
        return HallucinationResult(
            confidence=combined_confidence,
            risk_level=risk_level,
            layer_results=results,
            recommendations=generate_recommendations(results)
        )
    
    def store_validation_result(code_snippet, results):
        // Store in existing PostgreSQL schema
        validation_record = {
            'code_hash': calculate_hash(code_snippet),
            'timestamp': current_timestamp(),
            'validation_results': json.dumps(results),
            'confidence_score': calculate_weighted_confidence(results)
        }
        self.postgres_client.execute_query(
            "INSERT INTO hallucination_validations (code_hash, timestamp, results, confidence) VALUES (%s, %s, %s, %s)",
            validation_record.values()
        )
```

### New File: `backend/classifier/hallucination_detection/pattern_detector.py`

```pseudocode
// Extract from regex_hallucination_detector.py
class PatternBasedDetector:
    def __init__():
        self.suspicious_patterns = load_pattern_definitions()
        self.confidence_weights = load_confidence_mapping()
    
    def detect_suspicious_patterns(code):
        findings = []
        
        for pattern_group in self.suspicious_patterns:
            for pattern in pattern_group['patterns']:
                matches = re.findall(pattern['regex'], code)
                
                if matches:
                    suspicion = SuspiciousPattern(
                        pattern_type=pattern_group['type'],
                        pattern_name=pattern['name'],
                        matches=matches,
                        confidence=pattern['confidence'],
                        line_numbers=find_line_numbers(code, matches)
                    )
                    findings.append(suspicion)
        
        return PatternDetectionResult(
            findings=findings,
            overall_suspicion=calculate_overall_suspicion(findings)
        )
```

### Modify: `New_Project/ai_hallucination_detector.py`

```pseudocode
// Enhance existing detector with multi-layered approach
class AIHallucinationDetector:
    def __init__():
        // ... existing init
        self.core_detector = CoreHallucinationDetector()
        self.pattern_detector = PatternBasedDetector()
        self.knowledge_graph_validator = KnowledgeGraphValidator()
    
    def detect_hallucination(code_snippet, context):
        // Use existing logic as base layer
        base_result = self.existing_detection_logic(code_snippet)
        
        // Add new detection layers
        core_result = self.core_detector.detect_hallucinations(code_snippet, context)
        pattern_result = self.pattern_detector.detect_suspicious_patterns(code_snippet)
        
        // Combine results
        combined_result = self.combine_detection_results([
            base_result,
            core_result,
            pattern_result
        ])
        
        return EnhancedHallucinationResult(
            is_hallucination=combined_result.is_suspicious,
            confidence=combined_result.confidence,
            detection_layers=combined_result.layer_details,
            recommendations=combined_result.recommendations
        )
```

## 4. Architecture Analysis Service

### New File: `backend/classifier/architecture_service.py`

```pseudocode
// Merge MCP hexagonal_architecture_analyzer.py with existing implementation
class UnifiedArchitectureAnalyzer:
    def __init__():
        self.mcp_analyzer = load_mcp_patterns()
        self.existing_analyzer = load_existing_patterns()
        self.confidence_threshold = 0.7
    
    def analyze_component(code_element):
        // Run both analyzers
        mcp_result = self.mcp_analyzer.analyze(code_element)
        existing_result = self.existing_analyzer.analyze(code_element)
        
        // Combine and validate results
        if mcp_result.confidence > self.confidence_threshold:
            primary_classification = mcp_result
            secondary_classification = existing_result
        else:
            primary_classification = existing_result
            secondary_classification = mcp_result
        
        return ArchitectureClassification(
            primary=primary_classification,
            secondary=secondary_classification,
            consensus=calculate_consensus(mcp_result, existing_result),
            architectural_layer=determine_layer(primary_classification),
            hexagonal_role=determine_hexagonal_role(primary_classification)
        )
    
    def classify_entire_codebase(parsed_codebase):
        classifications = {}
        
        for component in parsed_codebase.components:
            classification = self.analyze_component(component)
            classifications[component.id] = classification
        
        // Generate architectural insights
        insights = self.generate_architectural_insights(classifications)
        
        return CodebaseArchitectureAnalysis(
            component_classifications=classifications,
            architectural_insights=insights,
            layer_distribution=calculate_layer_distribution(classifications),
            potential_issues=identify_architectural_issues(classifications)
        )
```

## 5. AST Dependency Extraction Integration

### Modify: `backend/parser/ast_visitors.py`

```pseudocode
// Enhance existing AST visitor with dependency extraction from ast_dependency_extraction.py
class EnhancedASTVisitor(ast.NodeVisitor):
    def __init__():
        // ... existing init
        self.dependency_extractor = DependencyExtractor()
        self.relationship_tracker = RelationshipTracker()
    
    def visit_Import(node):
        // ... existing import processing
        
        // Add dependency extraction
        import_relationships = self.dependency_extractor.extract_import_relationships(node)
        self.relationship_tracker.add_relationships(import_relationships)
        
        return processed_import_node
    
    def visit_Call(node):
        // ... existing call processing
        
        // Extract call relationships
        call_relationships = self.dependency_extractor.extract_call_relationships(
            node, self.current_function, self.current_class
        )
        self.relationship_tracker.add_relationships(call_relationships)
        
        return processed_call_node
    
    def visit_ClassDef(node):
        // ... existing class processing
        
        // Extract inheritance relationships
        inheritance_relationships = self.dependency_extractor.extract_inheritance_relationships(node)
        self.relationship_tracker.add_relationships(inheritance_relationships)
        
        return processed_class_node
```

### New File: `backend/graph_builder/relationship_extractor.py`

```pseudocode
// Extract and adapt dependency extraction logic for PostgreSQL + Neo4j integration
class RelationshipExtractor:
    def __init__(postgres_client, neo4j_client):
        self.postgres_client = postgres_client
        self.neo4j_client = neo4j_client
        self.extracted_relationships = []
    
    def extract_all_relationships(parsed_components):
        relationships = {
            'imports': [],
            'function_calls': [],
            'method_calls': [], 
            'inheritance': [],
            'class_usage': [],
            'type_annotations': []
        }
        
        for component in parsed_components:
            if component.type == 'import':
                relationships['imports'].extend(self.extract_import_relationships(component))
            elif component.type == 'function_call':
                relationships['function_calls'].extend(self.extract_function_call_relationships(component))
            elif component.type == 'class':
                relationships['inheritance'].extend(self.extract_inheritance_relationships(component))
        
        return relationships
    
    def store_relationships_in_postgres(relationships):
        // Store relationship metadata in PostgreSQL for querying
        for relationship_type, relationship_list in relationships.items():
            for rel in relationship_list:
                self.postgres_client.execute_query(
                    """
                    INSERT INTO code_relationships (
                        relationship_type, source_component_id, target_component_id,
                        source_file, target_file, line_number, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (relationship_type, rel['source_id'], rel['target_id'], 
                     rel['source_file'], rel['target_file'], rel['line_number'], 
                     json.dumps(rel['metadata']))
                )
    
    def create_neo4j_relationships(relationships):
        // Create actual graph relationships in Neo4j
        cypher_queries = []
        
        for relationship_type, relationship_list in relationships.items():
            for rel in relationship_list:
                if relationship_type == 'imports':
                    query = self.generate_import_cypher(rel)
                elif relationship_type == 'function_calls':
                    query = self.generate_function_call_cypher(rel)
                elif relationship_type == 'inheritance':
                    query = self.generate_inheritance_cypher(rel)
                
                cypher_queries.append(query)
        
        // Execute queries in Neo4j
        for query in cypher_queries:
            self.neo4j_client.execute_query(query)
    
    def generate_import_cypher(import_rel):
        return f"""
        MATCH (source:File {{path: '{import_rel['source_file']}'}})
        MERGE (target:File {{module_name: '{import_rel['target_module']}'}})
        MERGE (source)-[:IMPORTS {{
            import_type: '{import_rel['import_type']}',
            imported_item: '{import_rel.get('imported_item', '')}',
            alias: '{import_rel.get('alias', '')}'
        }}]->(target)
        """
    
    def generate_function_call_cypher(call_rel):
        return f"""
        MATCH (caller:Function {{name: '{call_rel['caller_function']}', module: '{call_rel['caller_module']}'}})
        MERGE (called:Function {{name: '{call_rel['called_function']}'}})
        MERGE (caller)-[:CALLS {{
            line_number: {call_rel['line_number']},
            call_type: '{call_rel['call_type']}'
        }}]->(called)
        """
```

## 6. Enhanced Neo4j Integration

### Modify: `backend/graph_builder/neo4j_exporter.py`

```pseudocode
// Enhance with MCP patterns while maintaining Neo4j + PostgreSQL + Chroma architecture
class EnhancedNeo4jExporter:
    def __init__(neo4j_client, postgres_client, chroma_client):
        self.neo4j_client = neo4j_client        // Existing Neo4j for graph relationships
        self.postgres_client = postgres_client  // Existing PostgreSQL for structured data
        self.chroma_client = chroma_client      // Existing Chroma for vector embeddings
        self.metadata_enricher = MetadataEnricher(postgres_client, chroma_client)
    
    def export_with_metadata_enrichment(parsed_data):
        // Use existing Neo4j export logic
        basic_export_result = self.existing_export_logic(parsed_data)
        
        // Add metadata enrichment using PostgreSQL and Chroma
        for node in basic_export_result.nodes:
            // Get architectural metadata from PostgreSQL
            pg_metadata = self.postgres_client.get_component_metadata(node.id)
            
            // Get semantic similarity data from Chroma
            similar_components = self.chroma_client.find_similar(node.embedding, top_k=5)
            
            enriched_metadata = self.metadata_enricher.enrich_node(node, pg_metadata, similar_components)
            node.metadata.update(enriched_metadata)
        
        // Add architectural relationships to Neo4j
        architectural_relationships = self.create_architectural_relationships(parsed_data)
        
        // Add type validation relationships to Neo4j
        type_relationships = self.create_type_validation_relationships(parsed_data)
        
        // Store cross-references in PostgreSQL
        self.store_cross_references_in_postgres(basic_export_result)
        
        return EnhancedExportResult(
            nodes=basic_export_result.nodes,
            relationships=basic_export_result.relationships + architectural_relationships + type_relationships,
            metadata_summary=self.generate_metadata_summary()
        )
    
    def store_cross_references_in_postgres(export_result):
        // Store Neo4j node IDs with PostgreSQL component records for cross-referencing
        for node in export_result.nodes:
            self.postgres_client.execute_query(
                "UPDATE code_components SET neo4j_node_id = %s WHERE component_id = %s",
                (node.neo4j_id, node.component_id)
            )
    
    def create_architectural_relationships(parsed_data):
        relationships = []
        
        for component in parsed_data.components:
            // Get architectural classification from PostgreSQL
            arch_data = self.postgres_client.get_architectural_classification(component.id)
            
            if arch_data:
                // Create Neo4j relationships for architectural layers
                layer_relationship = create_neo4j_relationship(
                    component.neo4j_id, 
                    f"BELONGS_TO_LAYER_{arch_data.layer.upper()}"
                )
                relationships.append(layer_relationship)
                
                // Create hexagonal role relationships
                hex_relationship = create_neo4j_relationship(
                    component.neo4j_id,
                    f"HAS_ROLE_{arch_data.hexagonal_role.upper()}"
                )
                relationships.append(hex_relationship)
        
        return relationships
```

## 6. Debug Utilities Integration

### Modify: `backend/parser/test_parser.py`

```pseudocode
// Enhance existing tests with MCP debug patterns
class EnhancedParserTests:
    def __init__():
        // ... existing test setup
        self.debug_utilities = DebugUtilities()
    
    def test_parsing_with_debug_analysis():
        // Run existing tests
        test_results = self.run_existing_tests()
        
        // Add debug analysis from MCP patterns
        debug_analysis = self.debug_utilities.analyze_parsing_issues(test_results)
        
        // Generate debug report
        debug_report = self.generate_debug_report(test_results, debug_analysis)
        
        assert test_results.all_passed
        return DebugTestResult(
            test_results=test_results,
            debug_analysis=debug_analysis,
            recommendations=debug_report.recommendations
        )
    
    def debug_ast_parsing_mismatches():
        // Use MCP debug_parser.py patterns
        python_files = get_test_files()
        
        for file_path in python_files[:10]:  // Test first 10 files
            ast_result = parse_with_ast(file_path)
            analyzer_result = parse_with_analyzer(file_path)
            
            if ast_result != analyzer_result:
                mismatch = analyze_parsing_mismatch(ast_result, analyzer_result)
                log_parsing_issue(file_path, mismatch)
```

### New File: `backend/api/debug_routes.py`

```pseudocode
// Create debug endpoints using MCP debug utilities
class DebugRoutes:
    def __init__(app):
        self.app = app
        self.debug_utilities = DebugUtilities()
        self.register_routes()
    
    def register_routes():
        @self.app.route('/debug/parsing')
        def debug_parsing_endpoint():
            repo_path = request.args.get('path', '.')
            debug_result = self.debug_utilities.debug_parsing(repo_path)
            return jsonify(debug_result)
        
        @self.app.route('/debug/database')
        def debug_database_endpoint():
            debug_result = self.debug_utilities.debug_neo4j_database()
            return jsonify(debug_result)
        
        @self.app.route('/debug/hallucination')
        def debug_hallucination_endpoint():
            code = request.json.get('code')
            context = request.json.get('context', {})
            debug_result = self.debug_utilities.debug_hallucination_detection(code, context)
            return jsonify(debug_result)
```

## 7. Configuration and Initialization

### New File: `backend/config/mcp_integration_config.py`

```pseudocode
// Configuration for MCP component integration with existing PostgreSQL/Chroma/Neo4j stack
class MCPIntegrationConfig:
    def __init__(postgres_client, chroma_client, neo4j_client):
        self.postgres_client = postgres_client
        self.chroma_client = chroma_client
        self.neo4j_client = neo4j_client
        
        self.hash_cache_enabled = get_env_bool('ENABLE_HASH_CACHE', True)
        self.hash_cache_path = get_env('HASH_CACHE_PATH', '.debug_tool_cache.json')
        self.stub_processing_enabled = get_env_bool('ENABLE_STUB_PROCESSING', True)
        self.hallucination_detection_layers = get_env_list('HALLUCINATION_LAYERS', 
            ['syntax', 'static_analysis', 'knowledge_graph', 'pattern', 'semantic'])
        self.architecture_analysis_mode = get_env('ARCHITECTURE_MODE', 'unified')
        
        // Use existing database configurations instead of Supabase/OpenAI
        self.embedding_model = get_env('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.postgres_schema = get_env('POSTGRES_SCHEMA', 'debug_tool')
        self.chroma_collection = get_env('CHROMA_COLLECTION', 'code_embeddings')
        
    def initialize_mcp_components():
        components = {}
        
        if self.hash_cache_enabled:
            components['file_tracker'] = FileChangeTracker(self.hash_cache_path)
        
        if self.stub_processing_enabled:
            components['stub_processor'] = StubFileProcessor()
        
        // Initialize with existing database clients
        components['hallucination_detector'] = CoreHallucinationDetector(
            postgres_client=self.postgres_client,
            chroma_client=self.chroma_client,
            enabled_layers=self.hallucination_detection_layers
        )
        
        components['architecture_analyzer'] = UnifiedArchitectureAnalyzer(
            postgres_client=self.postgres_client,
            mode=self.architecture_analysis_mode
        )
        
        components['enhanced_neo4j_exporter'] = EnhancedNeo4jExporter(
            neo4j_client=self.neo4j_client,
            postgres_client=self.postgres_client,
            chroma_client=self.chroma_client
        )
        
        return components
    
    def setup_database_schemas():
        // Create additional PostgreSQL tables for MCP integration
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS hallucination_validations (
                id SERIAL PRIMARY KEY,
                code_hash VARCHAR(64) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validation_results JSONB,
                confidence_score FLOAT,
                component_id INTEGER REFERENCES code_components(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS architectural_classifications (
                id SERIAL PRIMARY KEY,
                component_id INTEGER REFERENCES code_components(id),
                layer VARCHAR(50),
                hexagonal_role VARCHAR(50),
                confidence FLOAT,
                classification_method VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS file_change_tracking (
                id SERIAL PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_hash VARCHAR(64) NOT NULL,
                last_modified TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                project_id INTEGER
            );
            """
        ]
        
        for query in schema_queries:
            self.postgres_client.execute_query(query)
```

### Modify: `backend/main.py`

```pseudocode
// Initialize MCP components in main application with existing database clients
def initialize_application():
    // ... existing initialization of PostgreSQL, Chroma, Neo4j clients
    
    // Initialize MCP integration with existing database clients
    mcp_config = MCPIntegrationConfig(
        postgres_client=existing_postgres_client,
        chroma_client=existing_chroma_client,
        neo4j_client=existing_neo4j_client
    )
    
    // Setup additional database schemas for MCP features
    mcp_config.setup_database_schemas()
    
    // Initialize MCP components
    mcp_components = mcp_config.initialize_mcp_components()
    
    // Inject MCP components into existing services without breaking current functionality
    if hasattr(parser_service, 'set_file_tracker'):
        parser_service.set_file_tracker(mcp_components['file_tracker'])
    if hasattr(parser_service, 'set_stub_processor'):
        parser_service.set_stub_processor(mcp_components['stub_processor'])
    
    // Enhance existing classifier without replacing it
    if hasattr(classifier_service, 'add_hallucination_detector'):
        classifier_service.add_hallucination_detector(mcp_components['hallucination_detector'])
    if hasattr(classifier_service, 'set_architecture_analyzer'):
        classifier_service.set_architecture_analyzer(mcp_components['architecture_analyzer'])
    
    // Enhance existing graph builder
    if hasattr(graph_builder_service, 'set_enhanced_exporter'):
        graph_builder_service.set_enhanced_exporter(mcp_components['enhanced_neo4j_exporter'])
    
    // Register debug routes if in development mode
    if app.debug:
        debug_routes = DebugRoutes(app, mcp_components)
    
    return app
```

## Summary of Integration Strategy

### Files to Create:
1. `backend/infrastructure/file_change_tracker.py` - Hash-based change detection
2. `backend/parser/stub_processor.py` - .pyi file processing
3. `backend/classifier/hallucination_detection/` - Core detection algorithms
4. `backend/classifier/architecture_service.py` - Unified architecture analysis
5. `backend/graph_builder/relationship_extractor.py` - AST dependency extraction and Neo4j relationship creation
6. `backend/api/debug_routes.py` - Debug endpoints
7. `backend/config/mcp_integration_config.py` - Integration configuration

### Files to Modify:
1. `backend/parser/codebase_parser.py` - Add incremental parsing
2. `backend/parser/ast_visitors.py` - Enhance with stub processing
3. `backend/graph_builder/neo4j_exporter.py` - Add metadata enrichment
4. `backend/parser/test_parser.py` - Enhance with debug utilities
5. `New_Project/ai_hallucination_detector.py` - Add multi-layered detection
6. `backend/main.py` - Initialize MCP components

### Files to Adapt (replacing Supabase/OpenAI with PostgreSQL/Chroma):
1. `database_utils.py` - Replace Supabase calls with PostgreSQL queries and OpenAI embeddings with local sentence-transformers
2. `ast_dependency_extraction.py` - Integrate directly into existing AST processing pipeline with minimal changes
3. `debug_parser.py` - Use for development debugging (minimal changes needed)
4. `debug_database.py` - Adapt for Neo4j debugging with existing connection parameters

### Key Architecture Alignment Changes:

**Database Layer:**
- Replace Supabase → PostgreSQL for structured data storage
- Replace OpenAI embeddings → Local sentence-transformers or existing embedding model
- Maintain Neo4j for graph relationships (no change needed)
- Use Chroma for vector similarity search instead of Supabase vector storage

**Configuration:**
- Use existing environment variables and configuration patterns
- Integrate with existing database connection pooling
- Respect existing schema and table naming conventions

**Service Integration:**
- Add MCP components as optional enhancements to existing services
- Use dependency injection to avoid breaking existing functionality
- Maintain existing API contracts while adding new capabilities

**Data Flow:**
1. PostgreSQL stores structured component metadata and validation results
2. Chroma handles vector embeddings and semantic similarity
3. Neo4j manages graph relationships and architectural connections
4. File system tracks changes using hash-based caching

This integration approach maintains the existing PostgreSQL + Chroma + Neo4j architecture while enhancing it with proven patterns from the MCP project, focusing on incremental improvements and maintaining complete backward compatibility.