# AI Intent Tagging Rules for Python Code Analysis

## Overview
This document defines rules for AI systems to generate intent tags for Python code. These tags express architectural intent and enable comparison between intended design and actual implementation.

## Tag Syntax

# Generic Hexagonal Architecture Tagging System

## Core Node Labels

### Structural Nodes
```
:Codebase        // Root container for the entire codebase
:Module          // Logical grouping of related files  
:File            // Individual source code files
:Class           // Classes and interfaces
:Method          // Class methods
:Function        // Module-level functions
:Property        // Class properties/attributes
:Constant        // Module-level constants
:Variable        // Module-level variables
```

## Architectural Layer Labels

### Primary Layers (Hexagonal Rings)
```
:Core            // Inner hexagon - pure business logic
:Application     // Middle layer - application services and ports
:Infrastructure  // Outer layer - adapters and external concerns
```

### Layer Refinements
```
:Domain          // Core business domain (entities, value objects)
:Port            // Interfaces defining boundaries
:Adapter         // Concrete implementations of ports
:Utility         // Cross-cutting infrastructure concerns
```

## Hexagonal Role Labels

### Core Domain (Center of Hexagon)
```
:Entity          // Domain entities with identity
:ValueObject     // Immutable domain value objects
:Aggregate       // Aggregate roots managing consistency
:DomainService   // Domain logic that doesn't fit in entities
:DomainEvent     // Events representing domain occurrences
:Specification   // Domain rules and business logic
:Policy          // Business policies and rules
:Factory         // Domain object creation logic
```

### Application Layer (Orchestration)
```
:UseCase         // Application use case handlers
:Command         // Command objects (write operations)
:Query           // Query objects (read operations)
:CommandHandler  // Handlers for commands
:QueryHandler    // Handlers for queries
:ApplicationService // Application orchestration services
:Workflow        // Multi-step business workflows
:Saga            // Long-running business processes
```

### Ports (Interfaces)
```
:InboundPort     // Interfaces for incoming requests
:OutboundPort    // Interfaces for outgoing requests
:PrimaryPort     // Driving side interfaces (UI, API)
:SecondaryPort   // Driven side interfaces (database, external)
:EventPort       // Event publishing/subscribing interfaces
:NotificationPort // Notification sending interfaces
```

### Adapters (Implementations)
```
:PrimaryAdapter  // Driving adapters (controllers, CLI, UI)
:SecondaryAdapter // Driven adapters (database, external APIs)
:WebAdapter      // Web-based adapters
:DatabaseAdapter // Database access adapters
:MessagingAdapter // Message broker adapters
:FileAdapter     // File system adapters
:CacheAdapter    // Caching mechanism adapters
:SecurityAdapter // Authentication/authorization adapters
```

### Infrastructure Components
```
:Configuration   // Configuration and settings
:Logger          // Logging components
:Monitoring      // Metrics and health monitoring
:Security        // Security-related components
:Persistence     // Data persistence mechanisms
:Messaging       // Message brokers and queues
:Scheduler       // Task scheduling components
:Cache           // Caching mechanisms
:Validator       // Data validation components
:Serializer      // Data serialization components
```

## Technical Pattern Labels

### Design Patterns
```
:Singleton       // Singleton pattern implementations
:Factory         // Factory pattern implementations
:Builder         // Builder pattern implementations
:Strategy        // Strategy pattern implementations
:Observer        // Observer pattern implementations
:Decorator       // Decorator pattern implementations
:Proxy           // Proxy pattern implementations
:Repository      // Repository pattern implementations
:Gateway         // Gateway pattern implementations
:Facade          // Facade pattern implementations
```

### Architectural Patterns
```
:CQRS            // Command Query Responsibility Segregation
:EventSourcing   // Event sourcing components
:Microservice    // Microservice components
:API             // API-related components
:REST            // REST API components
:GraphQL         // GraphQL components
:RPC             // RPC components
:Batch           // Batch processing components
:Stream          // Stream processing components
```

## Quality Attribute Labels

### Behavioral Characteristics
```
:Async           // Asynchronous components
:Sync            // Synchronous components
:Stateless       // Stateless components
:Stateful        // Stateful components
:Immutable       // Immutable objects
:Mutable         // Mutable objects
:ThreadSafe      // Thread-safe components
:Idempotent      // Idempotent operations
:Transactional   // Transactional components
```

### Performance Characteristics
```
:Cacheable       // Components that cache data
:Distributed     // Distributed system components
:Scalable        // Horizontally scalable components
:HighThroughput  // High-throughput components
:LowLatency      // Low-latency components
:Resilient       // Fault-tolerant components
```

### Security Characteristics
```
:Authenticated   // Requires authentication
:Authorized      // Requires authorization
:Encrypted       // Handles encryption
:Audited         // Generates audit logs
:Sensitive       // Handles sensitive data
```

## Domain-Agnostic Functional Labels

### Data Operations
```
:Reader          // Components that read data
:Writer          // Components that write data
:Transformer     // Data transformation components
:Validator       // Data validation components
:Parser          // Data parsing components
:Generator       // Data generation components
:Aggregator      // Data aggregation components
:Filter          // Data filtering components
:Mapper          // Data mapping components
```

### Communication
```
:Publisher       // Event/message publishers
:Subscriber      // Event/message subscribers
:Client          // External service clients
:Server          // Server components
:Handler         // Request/event handlers
:Router          // Request routing components
:Middleware      // Middleware components
```

### Control Flow
```
:Controller      // Flow control components
:Coordinator     // Coordination components
:Orchestrator    // Orchestration components
:Dispatcher      // Request dispatching components
:Scheduler       // Scheduling components
:Manager         // Resource management components
```

## File and Module Labels

### File Types
```
:ImplementationFile // .py, .js, etc. - actual code
:TypeDefinitionFile // .pyi, .d.ts, etc. - type definitions
:ConfigurationFile  // Configuration files
:SchemaFile        // Data schema definitions
:MigrationFile     // Database migrations
:TestFile          // Test files
:DocumentationFile // Documentation files
```

### Module Classifications
```
:DomainModule      // Core business logic modules
:ApplicationModule // Application service modules
:InfrastructureModule // Infrastructure modules
:SharedModule      // Shared utility modules
:IntegrationModule // External integration modules
:TestModule        // Test modules
```

## Relationship Labels

### Structural Relationships
```
:CONTAINS          // Container contains component
:DEFINES           // File defines class/function
:DECLARES          // Declares interface/type
:HAS_METHOD        // Class has method
:HAS_PROPERTY      // Class has property
:HAS_ATTRIBUTE     // Object has attribute
:INHERITS_FROM     // Inheritance relationship
:IMPLEMENTS        // Interface implementation
:EXTENDS           // Extension relationship
:COMPOSES          // Composition relationship
:AGGREGATES        // Aggregation relationship
```

### Behavioral Relationships
```
:CALLS             // Method/function calls
:INVOKES           // Service invocation
:USES              // Component usage
:DEPENDS_ON        // Dependency relationship
:REQUIRES          // Required dependency
:PROVIDES          // Service provision
:CONSUMES          // Resource consumption
:PRODUCES          // Resource production
:TRANSFORMS        // Data transformation
:VALIDATES         // Validation relationship
```

### Architectural Relationships
```
:ADAPTS            // Adapter pattern relationship
:ORCHESTRATES      // Orchestration relationship
:COORDINATES       // Coordination relationship
:MANAGES           // Management relationship
:CONTROLS          // Control relationship
:MONITORS          // Monitoring relationship
:CONFIGURES        // Configuration relationship
:SECURES           // Security relationship
:CACHES            // Caching relationship
:PERSISTS          // Persistence relationship
```

### Port-Adapter Relationships
```
:ACCEPTS           // Port accepts requests
:SENDS_TO          // Sends requests to external
:ROUTES_TO         // Routes requests
:HANDLES           // Handles requests/events
:PUBLISHES         // Publishes events/messages
:SUBSCRIBES_TO     // Subscribes to events/messages
:CONNECTS_TO       // Connects to external system
:WRAPS             // Wraps external component
```

### Data Flow Relationships
```
:READS_FROM        // Reads data from source
:WRITES_TO         // Writes data to destination
:FLOWS_TO          // Data flow direction
:PROCESSES         // Data processing
:ENRICHES          // Data enrichment
:FILTERS           // Data filtering
:AGGREGATES_FROM   // Data aggregation source
:MAPS_TO           // Data mapping relationship
```

### Event Relationships
```
:TRIGGERS          // Triggers event/action
:RESPONDS_TO       // Responds to event
:LISTENS_TO        // Listens for events
:EMITS             // Emits events
:HANDLES_EVENT     // Handles specific events
:PROPAGATES        // Event propagation
```

### Quality Relationships
```
:VALIDATES_WITH    // Validation relationship
:SECURES_WITH      // Security mechanism
:MONITORS_WITH     // Monitoring relationship
:LOGS_TO           // Logging destination
:CACHES_WITH       // Caching mechanism
:ENCRYPTS_WITH     // Encryption mechanism
:AUDITS_WITH       // Audit mechanism
```

### Type and Stub Relationships
```
:TYPE_VALIDATES    // Type validation relationship
:STUBS_FOR         // Type stub for implementation
:TYPE_DEFINES      // Type definition relationship
:SIGNATURE_MATCHES // Signature compatibility
:TYPE_COMPATIBLE   // Type compatibility
```

## Usage Patterns

### Basic Tagging Pattern
```
Primary Layer + Role + Pattern + Quality Attributes

Example combinations:
:Core:Domain:Entity:Immutable
:Application:UseCase:CQRS:Async
:Infrastructure:Adapter:Database:Cacheable
```

### Relationship Pattern
```
Source -[:RELATIONSHIP_TYPE]-> Target

Example flows:
(Controller:PrimaryAdapter) -[:CALLS]-> (UseCase:Application)
(UseCase:Application) -[:USES]-> (Repository:SecondaryPort)
(RepositoryImpl:SecondaryAdapter) -[:IMPLEMENTS]-> (Repository:SecondaryPort)
```

### Query Pattern Examples
```
// Find all core domain components
MATCH (c:Core:Domain)
RETURN c

// Find architectural violations
MATCH (core:Core) -[:DEPENDS_ON]-> (infra:Infrastructure)
WHERE NOT infra:Port
RETURN core, infra

// Find all adapters for a port
MATCH (adapter:Adapter) -[:IMPLEMENTS]-> (port:Port)
RETURN port, collect(adapter)
```

This generic system provides a comprehensive foundation for modeling any hexagonal architecture while maintaining clear separation of concerns and enabling powerful architectural analysis.

### Basic Format
```python
# @intent: <layer>:<role>:<pattern>:<constraints>
# @implements: <interface_or_port_name>
# @depends-on: <comma_separated_allowed_dependencies>
# @data-flow: <input> -> <transformation> -> <output>
# @business-rule: <natural_language_rule>
# @performance: <requirement_with_metric>
# @security: <security_requirement>
# @version: <version_when_intent_defined>
```

### Tag Placement Rules
1. **Class-level tags**: Place immediately before class definition
2. **Function/Method tags**: Place immediately before function definition
3. **Module-level tags**: Place at top of file after imports
4. **Inline tags**: Use for specific code blocks needing intent clarification

## Layer Classification Rules

### Rule 1: Core Domain Layer Detection
```
IF code contains:
  - Business logic without external dependencies
  - Domain-specific calculations or rules
  - Entity relationships and invariants
  - Value objects or domain events
THEN assign @intent: core:<role>

Roles:
  - entity (has identity, lifecycle)
  - value-object (immutable, no identity)
  - aggregate (consistency boundary)
  - domain-service (stateless business logic)
  - domain-event (something that happened)
  - specification (business rule)
```

### Rule 2: Application Layer Detection
```
IF code contains:
  - Use case orchestration
  - Transaction boundaries
  - Application-specific logic
  - Command/Query handling
THEN assign @intent: application:<role>

Roles:
  - use-case (orchestrates domain logic)
  - command (write operation)
  - query (read operation)
  - command-handler (processes commands)
  - query-handler (processes queries)
  - application-service (app-specific operations)
  - saga (long-running process)
```

### Rule 3: Infrastructure Layer Detection
```
IF code contains:
  - External system integration
  - Database access
  - File I/O operations
  - Network communication
  - Framework-specific code
THEN assign @intent: infrastructure:<role>

Roles:
  - adapter (implements port)
  - repository (data persistence)
  - gateway (external service access)
  - controller (HTTP/API handling)
  - message-broker (async communication)
  - cache (performance optimization)
  - configuration (settings management)
```

## Pattern Detection Rules

### Rule 4: Design Pattern Recognition
```
Analyze structure and behavior:

IF single instance with global access:
  ADD :singleton

IF creates objects without specifying exact classes:
  ADD :factory

IF encapsulates object creation logic:
  ADD :builder

IF provides unified interface to subsystem:
  ADD :facade

IF encapsulates algorithm family:
  ADD :strategy

IF manages object lifecycle and access:
  ADD :repository

IF adapts interface to another:
  ADD :adapter

IF acts as placeholder for another object:
  ADD :proxy
```

### Rule 5: Architectural Pattern Recognition
```
IF separates read and write operations:
  ADD :cqrs

IF stores state changes as events:
  ADD :event-sourcing

IF provides API endpoints:
  ADD :rest OR :graphql

IF handles batch operations:
  ADD :batch

IF processes data streams:
  ADD :stream
```

## Constraint Detection Rules

### Rule 6: Quality Attribute Constraints
```
Behavioral Constraints:
  IF no await/async/threading: ADD :sync
  IF uses async/await: ADD :async
  IF no instance variables modified: ADD :stateless
  IF modifies instance variables: ADD :stateful
  IF no attribute modification after init: ADD :immutable
  IF thread synchronization present: ADD :thread-safe

Performance Constraints:
  IF caching logic present: ADD :cacheable
  IF distributed system markers: ADD :distributed
  IF performance-critical markers: ADD :low-latency
  IF high-throughput markers: ADD :high-throughput

Security Constraints:
  IF authentication checks: ADD :authenticated
  IF authorization checks: ADD :authorized
  IF encryption/decryption: ADD :encrypted
  IF audit logging: ADD :audited
  IF handles PII/credentials: ADD :sensitive
```

## Dependency Analysis Rules

### Rule 7: Import Classification
```
Categorize imports:

Standard Library:
  IF import from [os, sys, json, ...]: 
    CLASSIFY as standard-library

External Dependencies:
  IF import from pip packages:
    CLASSIFY as external-dependency
    CHECK if infrastructure concern

Internal Dependencies:
  IF import from same package:
    ANALYZE layer relationship
    FLAG if violates hierarchy

Allowed Dependencies:
  core -> core only
  application -> core, application
  infrastructure -> all layers
```

### Rule 8: Dependency Violation Detection
```
IF core layer imports infrastructure:
  FLAG as "layer-violation:severe"
  
IF application directly imports infrastructure:
  FLAG as "layer-violation:moderate"
  
IF circular imports detected:
  FLAG as "circular-dependency"
  
IF external dependency in core:
  FLAG as "external-dependency-in-core"
```

## Business Rule Extraction

### Rule 9: Business Logic Identification
```
Look for:
  - Validation logic with business meaning
  - Calculations specific to domain
  - State transitions with business rules
  - Invariant enforcement

Format as:
  @business-rule: <subject> must <condition>
  @business-rule: <action> requires <precondition>
  @business-rule: <calculation> equals <formula>
```

## Data Flow Analysis

### Rule 10: Data Transformation Tracking
```
Trace data flow:
  - Input sources (parameters, files, network)
  - Transformations (calculations, mappings)
  - Output destinations (return, files, network)

Format as:
  @data-flow: request -> validation -> transformation -> response
  @data-flow: file -> parse -> process -> database
```

## Confidence Scoring Rules

### Rule 11: Confidence Assignment
```
High Confidence (0.9-1.0):
  - Explicit framework markers (decorators, base classes)
  - Clear naming conventions followed
  - Consistent pattern implementation
  - Existing intent tags present

Medium Confidence (0.6-0.8):
  - Partial pattern match
  - Some naming conventions
  - Mixed responsibilities
  - Ambiguous layer placement

Low Confidence (0.0-0.5):
  - No clear patterns
  - Generic naming
  - Mixed concerns
  - Complex dependencies
```

## Intent vs Implementation Comparison

### Rule 12: Drift Detection Algorithm
```python
def detect_drift(intent_tags, actual_implementation):
    drift_report = {
        'layer_violations': [],
        'dependency_violations': [],
        'pattern_mismatches': [],
        'constraint_violations': [],
        'severity': 'none'
    }
    
    # Compare intended layer vs actual layer
    if intent_tags.layer != actual_implementation.detected_layer:
        drift_report['layer_violations'].append({
            'intended': intent_tags.layer,
            'actual': actual_implementation.detected_layer,
            'severity': calculate_severity()
        })
    
    # Check dependency compliance
    for dep in actual_implementation.dependencies:
        if dep not in intent_tags.allowed_dependencies:
            drift_report['dependency_violations'].append({
                'illegal_dependency': dep,
                'severity': 'high' if crosses_layers() else 'medium'
            })
    
    # Validate pattern implementation
    if intent_tags.pattern:
        if not matches_pattern(actual_implementation, intent_tags.pattern):
            drift_report['pattern_mismatches'].append({
                'expected_pattern': intent_tags.pattern,
                'issue': describe_mismatch()
            })
    
    return drift_report
```

## Examples

### Example 1: Core Entity with Intent Tags
```python
# @intent: core:entity:aggregate:immutable
# @business-rule: Order total must equal sum of line items
# @business-rule: Order cannot be modified after confirmation
# @depends-on: core:value-object, core:domain-service
# @performance: total calculation < 10ms
class Order:
    """Order aggregate root maintaining consistency"""
    
    def __init__(self, order_id: str, customer_id: str):
        self._id = order_id
        self._customer_id = customer_id
        self._line_items = []
        self._status = OrderStatus.DRAFT
    
    def add_line_item(self, product_id: str, quantity: int, price: Money):
        if self._status != OrderStatus.DRAFT:
            raise BusinessRuleViolation("Cannot modify confirmed order")
        # Implementation
```

### Example 2: Application Use Case
```python
# @intent: application:use-case:command-handler:transactional
# @implements: CreateOrderUseCase
# @depends-on: core:entity, application:port, application:event
# @data-flow: command -> validation -> entity-creation -> event-publish -> response
# @performance: complete within 100ms
# @security: authenticated, authorized:create-order
class CreateOrderHandler:
    """Handles order creation commands"""
    
    def __init__(self, order_repo: OrderRepository, event_bus: EventBus):
        self._order_repo = order_repo
        self._event_bus = event_bus
    
    async def handle(self, command: CreateOrderCommand) -> OrderCreatedResponse:
        # Validate command
        # Create order entity
        # Save via repository
        # Publish event
        # Return response
```

### Example 3: Infrastructure Adapter
```python
# @intent: infrastructure:adapter:repository:postgres
# @implements: OrderRepository
# @depends-on: application:port
# @data-flow: entity -> sql-mapping -> database
# @performance: queries < 50ms
# @security: encrypted-connection
class PostgresOrderRepository:
    """PostgreSQL implementation of order repository"""
    
    def __init__(self, connection_pool: Pool):
        self._pool = connection_pool
    
    async def save(self, order: Order) -> None:
        # Map entity to SQL
        # Execute INSERT/UPDATE
        # Handle exceptions
```

## AI Implementation Guidelines

1. **Always scan for existing tags first** - Don't override developer intent
2. **Use context for inference** - Consider file location, imports, class names
3. **Apply multiple rules** - Tags can have multiple attributes
4. **Flag uncertainties** - Low confidence scores need human review
5. **Track tag evolution** - Version tags to monitor architectural drift
6. **Validate completeness** - Ensure all architectural components are tagged
7. **Report conflicts** - Highlight contradictions between intent and implementation

## Output Format for AI Systems

```json
{
  "file": "path/to/file.py",
  "tags": [
    {
      "element": "class:Order",
      "intent": "core:entity:aggregate:immutable",
      "implements": null,
      "depends_on": ["core:value-object", "core:domain-service"],
      "business_rules": [
        "Order total must equal sum of line items"
      ],
      "confidence": 0.95,
      "inferred": false
    }
  ],
  "violations": [
    {
      "type": "layer-violation",
      "element": "class:Order",
      "detail": "Core entity imports infrastructure",
      "severity": "high"
    }
  ],
  "suggestions": [
    {
      "element": "method:calculate_total",
      "suggestion": "Add performance constraint tag",
      "reason": "Complex calculation without performance specification"
    }
  ]
}
```

This rule system enables AI to consistently analyze Python code architecture, detect intent-implementation drift, and maintain architectural integrity across evolving codebases.

---

# Neo4j Graph Modeling Enhancement Recommendations

*Based on comprehensive Neo4j documentation research and current implementation analysis (January 2025)*

## Enhanced Node Labels for Graph Database Optimization

These additional labels are specifically designed to optimize graph database storage, querying, and analysis:

### Hierarchical Package Structure Labels
```
:Package          // Top-level package containers (enables hierarchical queries)
:Subpackage       // Nested package organization
:Module:PythonFile // Combined labels for multi-dimensional categorization
:Module:TestFile   // Test module distinction
:Module:ConfigFile // Configuration module distinction
```

### Code Analysis Enhancement Labels
```
:Complexity:Low      // Cyclomatic complexity <= 5
:Complexity:Medium   // Cyclomatic complexity 6-10
:Complexity:High     // Cyclomatic complexity > 10
:Coupling:Loose      // Few dependencies
:Coupling:Tight      // Many dependencies
:Cohesion:High       // Single responsibility
:Cohesion:Low        // Multiple responsibilities
:Hotspot             // Frequently changed files
:Legacy              // Legacy code requiring attention
:Critical            // Critical path components
```

### Performance and Quality Labels
```
:Performance:Optimized  // Performance-critical code
:Performance:Standard   // Standard performance requirements
:Quality:Tested        // Has comprehensive tests
:Quality:Documented    // Well-documented
:Quality:Reviewed      // Code review completed
:Technical:Debt        // Technical debt markers
:Refactoring:Candidate // Needs refactoring
```

## Enhanced Relationship Types with Metadata

### Rich Relationship Properties Pattern
All relationships should include metadata for advanced analysis:

```cypher
// Enhanced relationship with metadata
(:Function)-[:CALLS {
  frequency: 15,           // How often called
  confidence: 0.95,        // Detection confidence
  line_number: 42,         // Source location
  complexity_added: 3,     // Complexity contribution
  last_modified: timestamp // Change tracking
}]->(:Function)

(:Class)-[:INHERITS_FROM {
  inheritance_type: "single",
  override_count: 3,
  interface_compliance: 0.87,
  pattern_type: "template_method"
}]->(:Class)
```

### New Advanced Relationship Types
```
// Architectural Analysis Relationships
:VIOLATES            // Architectural rule violations
:COMPLIES_WITH       // Architectural compliance
:SIMILAR_TO          // Code similarity (with similarity_score)
:TEMPORALLY_COUPLED  // Files changed together (with frequency)
:IMPLEMENTS_PATTERN  // Design pattern implementation
:CONTRIBUTES_TO      // Contribution relationship
:ABSTRACTS           // Abstraction relationship
:SPECIALIZES         // Specialization relationship

// Quality and Maintenance Relationships
:TESTS               // Test coverage relationship
:DOCUMENTS           // Documentation relationship
:BENCHMARKS          // Performance benchmark relationship
:MONITORS            // Monitoring relationship
:PROFILES            // Performance profiling relationship
:ANALYZES            // Static analysis relationship

// Temporal and Evolution Relationships
:REPLACES            // Replacement relationship
:EVOLVES_FROM        // Evolution tracking
:MIGRATES_TO         // Migration path
:DEPRECATES          // Deprecation relationship
:SUPERSEDES          // Superseding relationship

// Data and Information Flow
:SERIALIZES          // Data serialization
:DESERIALIZES        // Data deserialization
:TRANSFORMS_VIA      // Transformation pipeline
:ENRICHES_WITH       // Data enrichment
:AGGREGATES_VIA      // Aggregation mechanism
:PARTITIONS_BY       // Data partitioning
```

## Graph Algorithm Integration Tags

### Centrality Analysis Tags
```
:Centrality:Hub       // High out-degree (calls many)
:Centrality:Authority // High in-degree (called by many)
:Centrality:Bridge    // Connects different modules
:Centrality:Isolate   // Low connectivity
```

### Community Detection Tags
```
:Community:<ID>       // Belongs to community cluster
:Boundary:Component   // Component boundary element
:Internal:Component   // Internal to component
```

## Advanced Architectural Pattern Tags

### Microservices and Distributed Systems
```
:Service:Boundary     // Service boundary components
:Service:Internal     // Internal service components
:Circuit:Breaker      // Circuit breaker pattern
:Bulkhead            // Bulkhead isolation pattern
:Retry:Logic         // Retry mechanism
:Timeout:Handler     // Timeout handling
:Health:Check        // Health check endpoint
:Service:Discovery   // Service discovery
```

### Event-Driven Architecture
```
:Event:Producer      // Event producer
:Event:Consumer      // Event consumer
:Event:Router        // Event routing
:Event:Transformer   // Event transformation
:Event:Store         // Event storage
:Event:Replay        // Event replay capability
:Saga:Coordinator    // Saga coordination
:Compensation:Handler // Compensation action
```

### Data Pipeline and Analytics
```
:Pipeline:Source     // Data source
:Pipeline:Transform  // Data transformation
:Pipeline:Sink       // Data destination
:Stream:Processor    // Stream processing
:Batch:Processor     // Batch processing
:ETL:Component       // Extract-Transform-Load
:Data:Validator      // Data validation
:Schema:Enforcer     // Schema enforcement
```

## Neo4j Optimization Tagging Rules

### Rule 13: Graph Database Optimization Tags
```
IF class frequently queried by name:
  ADD :Indexed:Name
  SUGGEST: CREATE INDEX FOR (n:Class) ON n.name

IF relationship has high cardinality:
  ADD :High:Cardinality
  SUGGEST: Consider relationship properties for filtering

IF node has many properties:
  ADD :Property:Heavy
  SUGGEST: Consider property normalization

IF component is performance critical:
  ADD :Query:Critical
  SUGGEST: Optimize query paths and indexes
```

### Rule 14: Batch Processing Tags
```
IF component handles bulk operations:
  ADD :Batch:Optimized
  RECOMMEND: Use UNWIND for bulk operations
  RECOMMEND: Implement batching with periodic commits

IF component needs atomic operations:
  ADD :Transaction:Boundary
  RECOMMEND: Wrap in transaction scope
```

## Intent Tag Integration with Neo4j

### Rule 15: Graph-Aware Intent Validation
```python
def validate_graph_intent(node, intent_tags, graph_context):
    """
    Enhanced intent validation using graph context
    """
    validation_report = {
        'architectural_compliance': [],
        'graph_optimization_suggestions': [],
        'relationship_violations': [],
        'clustering_recommendations': []
    }
    
    # Check architectural compliance using graph structure
    if intent_tags.layer == 'core':
        outbound_deps = get_outbound_dependencies(node)
        for dep in outbound_deps:
            if dep.layer == 'infrastructure':
                validation_report['architectural_compliance'].append({
                    'violation': 'core_to_infrastructure_dependency',
                    'dependency': dep.name,
                    'severity': 'high',
                    'graph_path': get_shortest_path(node, dep)
                })
    
    # Analyze clustering and suggest architectural improvements
    community = detect_community(node, graph_context)
    if community.modularity < threshold:
        validation_report['clustering_recommendations'].append({
            'suggestion': 'consider_module_restructuring',
            'current_modularity': community.modularity,
            'related_components': community.members
        })
    
    return validation_report
```

## Implementation Priority for AI Systems

### Phase 1: Core Graph Enhancement (Immediate)
1. **Hierarchical Labels**: Add Package->Module->Class hierarchy
2. **Rich Relationships**: Include metadata in all relationships
3. **Performance Tags**: Add complexity and performance labels
4. **Basic Graph Algorithms**: Implement centrality and clustering

### Phase 2: Advanced Analysis (Short-term)
1. **Pattern Detection**: Advanced architectural pattern recognition
2. **Quality Integration**: Connect with code quality metrics
3. **Temporal Analysis**: Track evolution and changes over time
4. **Optimization Suggestions**: Graph-based performance recommendations

### Phase 3: Intelligence Integration (Medium-term)
1. **Predictive Analysis**: Use graph structure for predictions
2. **Automated Refactoring**: Graph-guided refactoring suggestions
3. **Impact Analysis**: Change impact prediction using graph traversal
4. **Architectural Validation**: Continuous architectural compliance checking

## Enhanced Output Format for Neo4j Integration

```json
{
  "file": "path/to/file.py",
  "graph_nodes": [
    {
      "id": "order_entity_123",
      "labels": ["Core", "Entity", "Aggregate", "Complexity:Medium"],
      "properties": {
        "name": "Order",
        "file_path": "core/entities/order.py",
        "lines_of_code": 145,
        "complexity_score": 7,
        "last_modified": "2025-01-21T04:30:00Z",
        "intent_compliance": 0.95
      }
    }
  ],
  "graph_relationships": [
    {
      "source": "order_entity_123",
      "target": "customer_entity_456",
      "type": "REFERENCES",
      "properties": {
        "frequency": 25,
        "confidence": 0.98,
        "line_number": 23,
        "relationship_strength": "strong",
        "architectural_compliance": true
      }
    }
  ],
  "graph_metrics": {
    "centrality_score": 0.75,
    "clustering_coefficient": 0.83,
    "community_id": "order_management_cluster",
    "architectural_distance": 2
  },
  "optimization_suggestions": [
    {
      "type": "index_recommendation",
      "suggestion": "Create composite index on (name, status) for Order queries",
      "estimated_performance_gain": "40%"
    },
    {
      "type": "relationship_optimization",
      "suggestion": "Use UNWIND for bulk order processing",
      "affected_operations": ["bulk_create", "bulk_update"]
    }
  ]
}
```

These enhancements integrate the AI tagging system with Neo4j graph database capabilities, enabling sophisticated architectural analysis, performance optimization, and continuous compliance monitoring while maintaining the existing hexagonal architecture foundation.