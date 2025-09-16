# Knowledge Module Design

## Overview

The Knowledge Module is a multi-store knowledge management system that enables agents to maintain specialized domain expertise while sharing common knowledge. It synthesizes, stores, and queries knowledge from multiple document sources across independent knowledge stores, implementing a sophisticated pipeline for document processing, graph construction, and information retrieval while maintaining source attribution and detecting contradictions.

## Requirements Coverage

This module addresses the following requirements:
- **MKS-001 to MKS-008**: Multi-knowledge store capabilities (PRIMARY)
- **SYN-001 to SYN-009**: Synthesis pipeline requirements
- **KGO-001 to KGO-007**: Knowledge graph operations requirements

## Module Structure

```
knowledge/
├── __init__.py           # Public API exports
├── registry.py           # Store registry (CORE component)
├── store.py              # Individual store implementation
├── synthesizer.py        # Store-specific document processing
├── graph.py              # Store-specific graph operations
├── agent_connector.py    # Agent-to-store interface (CORE)
├── config.py             # Store configurations and mappings
├── triage.py             # Document filtering and relevance
├── migration.py          # Single-to-multi store migration
├── exporters/            # Export format handlers
│   ├── __init__.py
│   ├── json_exporter.py
│   ├── graphml_exporter.py
│   └── rdf_exporter.py
└── tests/                # Module tests
    ├── test_registry.py
    ├── test_multi_store.py
    ├── test_synthesizer.py
    ├── test_graph.py
    └── test_migration.py
```

## Component Specifications

### Store Registry Component (CORE)

**Purpose**: Central management of multiple knowledge stores and their lifecycle

**Class Design**:
```python
class KnowledgeStoreRegistry:
    """Central registry managing all knowledge stores"""

    def __init__(self, config: RegistryConfig):
        self.stores: Dict[str, KnowledgeStore] = {}
        self.config = config
        self._initialize_default_stores()

    def get_store(self, name: str = "shared") -> KnowledgeStore:
        """Get or create a knowledge store"""
        if name not in self.stores:
            self.stores[name] = self._create_store(name)
        return self.stores[name]

    def create_store(
        self,
        name: str,
        config: StoreConfig
    ) -> KnowledgeStore:
        """Create a new specialized store"""

    def get_stores_for_agent(
        self,
        agent_name: str
    ) -> List[KnowledgeStore]:
        """Get all stores accessible to an agent"""

    def query_across_stores(
        self,
        query: str,
        store_names: List[str] = None
    ) -> Dict[str, List[KnowledgeNode]]:
        """Query multiple stores in parallel"""
```

### Agent Connector Component (CORE)

**Purpose**: Simplify agent access to their knowledge domains

**Class Design**:
```python
class AgentKnowledgeConnector:
    """Agent-specific knowledge interface"""

    def __init__(
        self,
        agent_name: str,
        registry: KnowledgeStoreRegistry
    ):
        self.agent_name = agent_name
        self.registry = registry
        self.stores = self._load_agent_stores()
        self.primary_store = self._determine_primary_store()

    async def query(
        self,
        query: str,
        stores: Optional[List[str]] = None
    ) -> List[KnowledgeNode]:
        """Query across agent's knowledge stores"""

    async def synthesize(
        self,
        documents: List[Document],
        store: Optional[str] = None
    ) -> KnowledgeGraph:
        """Synthesize documents into appropriate store"""

    async def add_knowledge(
        self,
        node: KnowledgeNode,
        store: Optional[str] = None
    ) -> None:
        """Add knowledge to appropriate store"""
```

### Synthesizer Component

**Purpose**: Process documents into structured knowledge for a specific store

**Class Design**:
```python
class KnowledgeSynthesizer:
    """Store-specific document processing pipeline"""

    def __init__(
        self,
        config: SynthesizerConfig,
        store_name: str = "shared"
    ):
        self.store_name = store_name
        self.triage = TriageEngine(config.triage_settings)
        self.extractors = self._load_extractors(config.extractors)
        self.integrator = Integrator()

    async def synthesize(
        self,
        documents: List[Document],
        query: Optional[str] = None,
        target_store: Optional[KnowledgeStore] = None
    ) -> KnowledgeGraph:
        """Process documents into knowledge graph for specific store"""

    async def synthesize_incremental(
        self,
        documents: List[Document],
        existing_graph: KnowledgeGraph,
        target_store: Optional[KnowledgeStore] = None
    ) -> KnowledgeGraph:
        """Update existing graph with new documents"""
```

**Key Methods**:
- `triage_documents()`: Filter and rank documents
- `extract_knowledge()`: Extract structured data
- `integrate_sources()`: Merge information from multiple sources
- `detect_conflicts()`: Identify contradictions

### Graph Component

**Purpose**: Manage store-specific graph operations and queries

**Class Design**:
```python
class KnowledgeGraph:
    """Store-specific graph data structure and operations"""

    def __init__(self, store_name: str = "shared"):
        self.store_name = store_name
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[Edge] = []
        self.index = GraphIndex(store_name)
        self.metadata = GraphMetadata(store_name)

    def add_node(self, node: KnowledgeNode) -> None:
        """Add node with automatic indexing and store tagging"""
        node.store_origin = self.store_name
        # Add node logic

    def find_paths(
        self,
        start: str,
        end: str,
        max_length: int = 5,
        cross_store: bool = False
    ) -> List[Path]:
        """Find paths between nodes, optionally across stores"""

    def get_neighborhood(
        self,
        node_id: str,
        hops: int = 2,
        include_shared: bool = True
    ) -> Subgraph:
        """Extract subgraph around node"""

    def find_contradictions(
        self,
        other_graphs: List['KnowledgeGraph'] = None
    ) -> List[Contradiction]:
        """Detect contradictions within store or across stores"""

    def merge_from(
        self,
        other_graph: 'KnowledgeGraph',
        conflict_resolution: str = "newest"
    ) -> None:
        """Merge knowledge from another graph"""
```

**Query Interface**:
```python
class GraphQuery:
    """Fluent query interface for multi-store graphs"""

    def __init__(self, stores: List[str] = None):
        self.target_stores = stores or ["shared"]
        self.cross_store = len(self.target_stores) > 1

    def nodes(self) -> 'GraphQuery':
        """Start node query"""

    def edges(self) -> 'GraphQuery':
        """Start edge query"""

    def in_stores(self, stores: List[str]) -> 'GraphQuery':
        """Specify which stores to query"""

    def where(self, condition: Callable) -> 'GraphQuery':
        """Filter results"""

    def with_attribution(self) -> 'GraphQuery':
        """Include store origin in results"""

    def limit(self, n: int) -> 'GraphQuery':
        """Limit results per store"""

    def execute(self) -> QueryResult:
        """Execute query across specified stores"""
```

### Store Component

**Purpose**: Individual knowledge store with isolated persistence and indexing

**Class Design**:
```python
class KnowledgeStore:
    """Individual knowledge store with complete isolation"""

    def __init__(
        self,
        storage_path: Path,
        store_name: str,
        config: StoreConfig
    ):
        self.store_name = store_name
        self.config = config
        self.path = storage_path / "stores" / store_name
        self.path.mkdir(parents=True, exist_ok=True)
        self.metadata = self._load_metadata()
        self.graph = KnowledgeGraph(store_name)
        self.synthesizer = KnowledgeSynthesizer(config.synthesis_config, store_name)
        self._init_indices()

    async def save(
        self,
        graph: Optional[KnowledgeGraph] = None,
        version: Optional[str] = None
    ) -> str:
        """Persist this store's graph with versioning"""
        if graph is None:
            graph = self.graph
        # Store-specific persistence

    async def load(
        self,
        version: Optional[str] = None
    ) -> KnowledgeGraph:
        """Load this store's graph"""

    async def query(
        self,
        query: str,
        limit: int = 10
    ) -> List[KnowledgeNode]:
        """Query within this store"""

    async def synthesize_documents(
        self,
        documents: List[Document]
    ) -> KnowledgeGraph:
        """Synthesize documents into this store"""
        return await self.synthesizer.synthesize(
            documents,
            target_store=self
        )

    def clear_store(self) -> None:
        """Clear all data from this store only"""

    def get_statistics(self) -> StoreStatistics:
        """Get store-specific statistics"""
```

**Storage Structure**:
```
.data/knowledge/
├── stores/
│   ├── shared/           # Shared knowledge store
│   │   ├── metadata.json
│   │   ├── graph.json
│   │   ├── vectors/
│   │   └── indices/
│   ├── architecture/     # Architecture-specific store
│   │   ├── metadata.json
│   │   ├── graph.json
│   │   ├── vectors/
│   │   └── indices/
│   ├── security/         # Security-specific store
│   │   └── ...
│   └── [agent_name]/     # Agent-specific stores
│       └── ...
├── registry.json         # Store registry metadata
└── config.yaml          # Store configurations
```

**Store Format**:
```json
{
    "metadata": {
        "store_name": "architecture",
        "version": "v1.0",
        "created": "2024-01-20T10:00:00Z",
        "node_count": 1500,
        "edge_count": 3200,
        "agents": ["zen-architect", "refactor-architect"]
    },
    "nodes": [
        {
            "id": "node_1",
            "type": "concept",
            "content": "...",
            "store_origin": "architecture",
            "properties": {}
        }
    ],
    "edges": [
        {
            "source": "node_1",
            "target": "node_2",
            "predicate": "relates_to",
            "weight": 0.8,
            "store_origin": "architecture"
        }
    ]
}
```

### Triage Component

**Purpose**: Filter and rank documents by relevance for specific stores

**Class Design**:
```python
class TriageEngine:
    """Store-aware document filtering and relevance scoring"""

    def __init__(self, config: TriageConfig):
        self.scorers = self._load_scorers(config)
        self.threshold = config.relevance_threshold
        self.store_rules = config.store_specific_rules

    async def triage(
        self,
        documents: List[Document],
        query: str,
        target_store: str = "shared"
    ) -> List[RankedDocument]:
        """Filter and rank documents for specific store"""

    def score_relevance(
        self,
        document: Document,
        query: str,
        store_context: StoreConfig
    ) -> float:
        """Calculate store-specific relevance score"""

    def determine_target_stores(
        self,
        document: Document
    ) -> List[str]:
        """Determine which stores should receive this document"""
```

**Store-Specific Scoring**:
- Store domain keywords
- Agent expertise matching
- Cross-store reference detection
- Store-specific rules

## Data Models

### Store Configuration Models

```python
@dataclass
class StoreConfig:
    """Configuration for a knowledge store"""
    name: str
    description: str
    persistence: bool = True
    vector_enabled: bool = True
    max_size_mb: int = 1000
    agents: List[str] = field(default_factory=list)
    shared_access: bool = False
    synthesis_config: SynthesizerConfig = None
    auto_backup: bool = True

@dataclass
class AgentStoreMapping:
    """Maps agents to their accessible stores"""
    agent_name: str
    primary_store: str
    secondary_stores: List[str]
    read_only_stores: List[str] = field(default_factory=list)
```

### Core Models

```python
@dataclass
class KnowledgeNode:
    """Node in knowledge graph"""
    id: str
    type: NodeType
    content: str
    properties: Dict[str, Any]
    source_ids: List[str]
    confidence: float
    created_at: datetime
    store_origin: str = "shared"  # Store this node belongs to
    cross_store_refs: List[str] = field(default_factory=list)

@dataclass
class Edge:
    """Relationship between nodes"""
    source_id: str
    target_id: str
    predicate: str
    weight: float
    properties: Dict[str, Any]
    source_ids: List[str]
    store_origin: str = "shared"  # Store this edge belongs to
    cross_store: bool = False  # True if connects nodes in different stores

@dataclass
class Contradiction:
    """Detected contradiction in graph"""
    node_ids: List[str]
    edge_ids: List[str]
    stores_involved: List[str]  # Which stores contain conflicting info
    description: str
    severity: float
    resolution_suggestions: List[str]

@dataclass
class StoreStatistics:
    """Statistics for a knowledge store"""
    store_name: str
    node_count: int
    edge_count: int
    total_size_mb: float
    last_updated: datetime
    agent_access_count: Dict[str, int]
```

## Processing Pipeline

### Multi-Store Synthesis Flow

```
1. Document Input
   │
   ├─→ Store Selection
   │   ├─→ Agent Context
   │   ├─→ Document Domain
   │   └─→ Store Rules
   │
   ├─→ Triage (Per Store)
   │   ├─→ Store-specific Relevance
   │   └─→ Filtering
   │
   ├─→ Extraction
   │   ├─→ Entity Extraction
   │   ├─→ Relationship Extraction
   │   └─→ Property Extraction
   │
   ├─→ Store-Specific Integration
   │   ├─→ In-Store Entity Resolution
   │   ├─→ Cross-Store Reference Detection
   │   └─→ Conflict Detection
   │
   └─→ Store Graph Update
       ├─→ Store-Tagged Node Creation
       ├─→ Store-Tagged Edge Creation
       ├─→ Store Index Update
       └─→ Cross-Store Link Update
```

### Multi-Store Query Processing

```
1. Query Input
   │
   ├─→ Store Resolution
   │   ├─→ Agent Store Access
   │   ├─→ Query Store Hints
   │   └─→ Default Store Selection
   │
   ├─→ Query Distribution
   │   ├─→ Parallel Store Queries
   │   ├─→ Store-Specific Parsing
   │   └─→ Cross-Store Coordination
   │
   ├─→ Per-Store Processing
   │   ├─→ Store Index Lookup
   │   ├─→ Store Graph Traversal
   │   └─→ Store Result Collection
   │
   ├─→ Result Aggregation
   │   ├─→ Cross-Store Deduplication
   │   ├─→ Store Priority Weighting
   │   └─→ Conflict Resolution
   │
   └─→ Unified Result
       ├─→ Combined Ranking
       ├─→ Store Attribution
       └─→ Result Limiting
```

## Integration Points

### Event Emissions

```python
# Events emitted by this module
EVENTS = {
    'knowledge.store_created': {
        'store_name': str,
        'config': StoreConfig,
        'agents': List[str]
    },
    'knowledge.document_triaged': {
        'document_id': str,
        'store_name': str,
        'relevance_score': float,
        'passed': bool
    },
    'knowledge.synthesized': {
        'store_name': str,
        'graph_id': str,
        'node_count': int,
        'edge_count': int,
        'source_count': int
    },
    'knowledge.contradiction_found': {
        'stores_involved': List[str],
        'contradiction_id': str,
        'severity': float,
        'node_ids': List[str]
    },
    'knowledge.cross_store_link': {
        'source_store': str,
        'target_store': str,
        'link_type': str
    },
    'knowledge.queried': {
        'query': str,
        'stores_queried': List[str],
        'result_count': int,
        'execution_time': float
    }
}
```

### External Dependencies

- `models`: Shared data models
- `events`: Event bus for notifications
- No direct dependencies on other application modules

## Configuration

### Module Configuration

```yaml
knowledge:
  # Multi-store configuration (PRIMARY)
  multi_store:
    enabled: true  # Always true - multi-store is the default
    default_store: "shared"
    auto_create_agent_stores: true

  # Store definitions
  stores:
    shared:
      description: "Common knowledge for all agents"
      persistence: true
      max_size_mb: 5000
      vector_enabled: true
      shared_access: true

    architecture:
      description: "Design patterns and principles"
      agents: ["zen-architect", "refactor-architect"]
      max_size_mb: 1000

    security:
      description: "Security vulnerabilities and patterns"
      agents: ["security-guardian"]
      max_size_mb: 500
      auto_update: true  # Pull OWASP updates

    performance:
      description: "Performance optimization patterns"
      agents: ["performance-optimizer"]
      max_size_mb: 750

    bugs:
      description: "Common bug patterns and fixes"
      agents: ["bug-hunter"]
      max_size_mb: 500

    testing:
      description: "Test patterns and strategies"
      agents: ["test-coverage"]
      max_size_mb: 500

  # Agent to store mappings
  agent_mappings:
    zen-architect:
      primary: "architecture"
      secondary: ["shared"]

    bug-hunter:
      primary: "bugs"
      secondary: ["shared", "testing"]

    security-guardian:
      primary: "security"
      secondary: ["shared"]
      read_only: ["architecture"]  # Can read but not write

  # Synthesis configuration (per-store overrideable)
  synthesis:
    batch_size: 100
    parallel_extractors: 4
    chunk_size: 1000  # tokens

  # Triage configuration (per-store overrideable)
  triage:
    relevance_threshold: 0.5
    keyword_weight: 0.3
    semantic_weight: 0.7

  # Storage paths
  storage:
    base_path: ./data/knowledge/
    version_retention: 10
    compression: true
    backup_interval: daily

  # Query configuration
  query:
    default_limit: 10
    max_limit: 1000
    timeout_seconds: 30
    parallel_store_queries: true

  # Export configuration
  export:
    formats: [json, graphml, rdf, gexf]
    max_export_size: 100MB
    per_store_export: true
```

## Performance Considerations

### Multi-Store Optimization Strategies

1. **Store Isolation**: Each store has independent resources
2. **Parallel Store Operations**: Process multiple stores concurrently
3. **Store-Specific Caching**: Cache per store, not globally
4. **Selective Store Loading**: Load only active stores
5. **Cross-Store Index**: Optimized index for cross-references
6. **Incremental Store Updates**: Update stores independently
7. **Store-Level Sharding**: Shard large stores across files

### Scalability Limits (Per Store)

- Maximum stores: 1000+
- Maximum nodes per store: 1M
- Maximum edges per store: 10M
- Cross-store links: 100K per store
- Query response time: < 500ms for 100K nodes
- Parallel store queries: Unlimited
- Synthesis throughput: 100 documents/minute/store

## Testing Strategy

### Unit Tests

```python
class TestStoreRegistry:
    """Test multi-store registry"""

    def test_create_multiple_stores(self):
        """Verify creation of independent stores"""

    def test_store_isolation(self):
        """Verify stores are properly isolated"""

    def test_agent_store_mapping(self):
        """Verify agents get correct store access"""

class TestMultiStoreSynthesis:
    """Test synthesis across stores"""

    def test_store_specific_synthesis(self):
        """Verify documents go to correct stores"""

    def test_cross_store_references(self):
        """Verify cross-store links are created"""
```

### Integration Tests

```python
class TestMultiStoreIntegration:
    """Test multi-store operations"""

    async def test_parallel_store_queries(self):
        """Test querying across multiple stores"""

    async def test_agent_knowledge_isolation(self):
        """Test agent-specific knowledge access"""

    async def test_cross_store_contradiction_detection(self):
        """Test finding contradictions across stores"""

    async def test_store_migration(self):
        """Test migration from single to multi-store"""
```

## Error Handling

### Exception Hierarchy

```python
class KnowledgeException(Exception):
    """Base exception for knowledge module"""

class SynthesisException(KnowledgeException):
    """Synthesis pipeline errors"""

class GraphException(KnowledgeException):
    """Graph operation errors"""

class StorageException(KnowledgeException):
    """Storage operation errors"""

class QueryException(KnowledgeException):
    """Query processing errors"""
```

### Recovery Strategies

- **Partial Failures**: Continue processing valid documents
- **Storage Errors**: Retry with exponential backoff
- **Query Timeouts**: Return partial results with warning
- **Corruption Detection**: Validate and repair graph structure

## Security Considerations

### Input Validation
- Sanitize document content
- Validate query parameters
- Check file sizes and formats
- Rate limit API requests

### Access Control
- Graph-level permissions
- Query result filtering
- Export restrictions
- Audit logging

## Future Enhancements

### Planned Features
1. **Dynamic Store Creation**: Auto-create stores based on document domains
2. **Store Federation**: Connect to remote knowledge stores
3. **Store Synchronization**: Sync stores across environments
4. **Machine Learning Integration**: Smart store selection and routing
5. **Real-time Store Updates**: WebSocket-based cross-store sync
6. **Distributed Store Processing**: Multi-node store management
7. **Store Analytics**: Per-store usage and performance metrics
8. **Natural Language Store Queries**: "What does the security store know about X?"

### Extension Points
- Custom store types via plugin system
- Additional store backends (vector DBs, graph DBs)
- Store-specific extractors and synthesizers
- Cross-store reasoning engines
- Store migration and merge tools

## Module Contract

### Inputs
- Documents with optional store targeting
- Agent-contextualized queries
- Store configurations and mappings
- Cross-store query specifications

### Outputs
- Store-specific knowledge graphs
- Multi-store query results with attribution
- Store-aware contradiction reports
- Per-store export data
- Store statistics and health metrics

### Side Effects
- Persists to `./data/knowledge/stores/[store_name]/`
- Creates store-specific indices
- Maintains cross-store reference links
- Emits store-aware events
- Logs per-store operations

### Guarantees
- Complete store isolation
- Thread-safe multi-store operations
- Atomic per-store updates
- Consistent cross-store references
- Backward compatibility with single-store API
- Graceful handling of store failures

## API Usage Examples

### Basic Multi-Store Usage

```python
# Initialize the registry (done once at startup)
registry = KnowledgeStoreRegistry(config)

# Get a specific store
arch_store = registry.get_store("architecture")

# Synthesize documents into a specific store
graph = await arch_store.synthesize_documents(documents)

# Query a specific store
results = await arch_store.query("design patterns")

# Query across multiple stores
stores_to_query = ["architecture", "shared"]
results = await registry.query_across_stores(
    "SOLID principles",
    store_names=stores_to_query
)
```

### Agent-Specific Usage

```python
# Agent initialization
class ZenArchitectAgent:
    def __init__(self):
        # Automatically gets architecture + shared stores
        self.knowledge = AgentKnowledgeConnector(
            "zen-architect",
            registry
        )

    async def analyze(self, code):
        # Query agent's stores (architecture + shared)
        patterns = await self.knowledge.query("design patterns")

        # Add to primary store (architecture)
        await self.knowledge.add_knowledge(
            KnowledgeNode("new_pattern", data)
        )

        # Query all accessible stores with attribution
        results = await self.knowledge.query(
            "microservices",
            stores=["architecture", "shared", "performance"]
        )
```

### Backward Compatible Usage

```python
# Old single-store API still works (uses shared store)
from knowledge import synthesize, query

# These route to the shared store by default
graph = await synthesize(documents)
results = await query("some query")

# Explicitly specify store for gradual migration
graph = await synthesize(documents, store="architecture")
```

### Cross-Store Operations

```python
# Find contradictions across stores
contradictions = await registry.find_cross_store_contradictions(
    stores=["security", "performance"]
)

# Merge knowledge from one store to another
arch_store = registry.get_store("architecture")
shared_store = registry.get_store("shared")
await shared_store.graph.merge_from(
    arch_store.graph,
    conflict_resolution="newest"
)

# Export specific stores
await registry.export_stores(
    store_names=["architecture", "security"],
    format="graphml"
)
```

## Migration Strategy

### Automatic Migration

```python
class MigrationManager:
    """Handles migration from single to multi-store"""

    async def migrate(self):
        # 1. Detect existing single-store data
        if self.has_legacy_data():
            # 2. Create shared store from existing data
            legacy_graph = await self.load_legacy_graph()
            shared_store = registry.create_store("shared", shared_config)
            await shared_store.save(legacy_graph)

        # 3. Initialize specialized stores
        for store_name, config in DEFAULT_STORES.items():
            if not registry.has_store(store_name):
                registry.create_store(store_name, config)

        # 4. Set up agent mappings
        await self.configure_agent_mappings()
```

### Gradual Migration Path

1. **Phase 1**: Continue using single-store API (routes to shared)
2. **Phase 2**: Create specialized stores, start routing new knowledge
3. **Phase 3**: Migrate existing knowledge to appropriate stores
4. **Phase 4**: Update agents to use multi-store API
5. **Phase 5**: Deprecate single-store API

## Performance Characteristics

### Multi-Store Optimizations

1. **Parallel Store Operations**: Query/update multiple stores concurrently
2. **Store-Level Caching**: Each store maintains independent cache
3. **Lazy Loading**: Stores loaded only when accessed
4. **Selective Indexing**: Per-store index optimization
5. **Memory Management**: Inactive stores can be unloaded

### Scalability

- Stores: Unlimited (practically ~1000s)
- Nodes per store: 1M
- Edges per store: 10M
- Parallel queries: Unlimited
- Cross-store links: 100K per store