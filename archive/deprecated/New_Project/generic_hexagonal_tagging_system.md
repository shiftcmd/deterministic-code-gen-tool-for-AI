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