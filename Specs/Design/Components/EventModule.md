# Event Module Design

## Overview

The Event Module provides comprehensive event logging, streaming, and analysis capabilities for system observability, debugging, and audit trails. It implements an append-only event log system with real-time streaming, filtering, replay, and analysis features.

## Requirements Coverage

This module addresses the following requirements:
- **EVT-LOG-*** : Event logging operations
- **EVT-FILT-*** : Event filtering and query capabilities
- **EVT-STRM-*** : Real-time event streaming
- **EVT-RPLY-*** : Event replay functionality
- **EVT-PIPE-*** : Pipeline event tracking
- **EVT-HOOK-*** : Hook execution events
- **EVT-PROC-*** : Processing operation events
- **EVT-STOR-*** : Event storage management
- **EVT-ANAL-*** : Event analysis and patterns

## Module Structure

```
events/
├── __init__.py           # Public API exports
├── logger.py             # Event logging core
├── store.py              # Event storage and rotation
├── streamer.py           # Real-time streaming
├── replay.py             # Event replay engine
├── filter.py             # Filtering and query
├── analyzer.py           # Event analysis and patterns
├── correlator.py         # Event correlation and chains
├── models.py             # Event data models
├── config.py             # Configuration management
├── exporters/            # Export format handlers
│   ├── __init__.py
│   ├── json_exporter.py
│   ├── csv_exporter.py
│   └── parquet_exporter.py
└── tests/                # Module tests
    ├── test_logger.py
    ├── test_store.py
    ├── test_streamer.py
    ├── test_replay.py
    └── test_analyzer.py
```

## Component Specifications

### EventLogger Component

**Purpose**: Core event logging functionality with structured data

**Class Design**:
```python
class EventLogger:
    """Central event logging system"""

    def __init__(self, config: EventConfig):
        self.store = EventStore(config.storage)
        self.streamer = EventStreamer()
        self.buffer = EventBuffer(config.buffer_size)
        self.correlation_tracker = CorrelationTracker()

    def log(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """Log an event with automatic timestamping and ID generation"""

    def log_batch(
        self,
        events: List[Event]
    ) -> List[str]:
        """Log multiple events atomically"""

    def with_correlation(
        self,
        correlation_id: str
    ) -> 'ContextualLogger':
        """Create logger with correlation context"""
```

**Key Methods**:
- `log()`: Primary logging interface
- `log_structured()`: Log with validation
- `log_error()`: Specialized error logging
- `flush()`: Force buffer flush

### EventStore Component

**Purpose**: Manage event persistence with rotation and indexing

**Class Design**:
```python
class EventStore:
    """Event storage with rotation and compression"""

    def __init__(self, config: StorageConfig):
        self.base_path = config.base_path
        self.current_log = self._get_current_log()
        self.index = EventIndex(config.index_path)
        self.rotator = LogRotator(config.rotation)
        self.compressor = LogCompressor()

    async def append(
        self,
        event: Event
    ) -> None:
        """Append event to current log"""

    async def query(
        self,
        filters: EventFilters,
        limit: Optional[int] = None
    ) -> List[Event]:
        """Query events with filters"""

    async def rotate_if_needed(self) -> None:
        """Check and perform log rotation"""

    async def archive_old_logs(
        self,
        older_than: datetime
    ) -> int:
        """Archive and compress old logs"""
```

**Storage Format**:
```json
{
    "id": "evt_1234567890",
    "timestamp": "2024-01-20T10:30:00Z",
    "type": "pipeline.stage.completed",
    "source": "synthesis_pipeline",
    "correlation_id": "pipe_abc123",
    "payload": {
        "stage": "extraction",
        "duration_ms": 1250,
        "items_processed": 10
    },
    "metadata": {
        "host": "worker-01",
        "version": "1.0.0"
    }
}
```

### EventStreamer Component

**Purpose**: Real-time event streaming with backpressure handling

**Class Design**:
```python
class EventStreamer:
    """Real-time event streaming engine"""

    def __init__(self):
        self.subscribers: Dict[str, StreamSubscriber] = {}
        self.buffers: Dict[str, asyncio.Queue] = {}
        self.backpressure_monitor = BackpressureMonitor()

    async def subscribe(
        self,
        subscriber_id: str,
        filters: Optional[EventFilters] = None,
        buffer_size: int = 1000
    ) -> StreamSubscriber:
        """Subscribe to event stream"""

    async def publish(
        self,
        event: Event
    ) -> None:
        """Publish event to subscribers"""

    async def stream(
        self,
        subscriber_id: str
    ) -> AsyncIterator[Event]:
        """Stream events to subscriber"""

    def handle_slow_consumer(
        self,
        subscriber_id: str
    ) -> None:
        """Handle backpressure from slow consumers"""
```

**Streaming Patterns**:
- Fan-out to multiple consumers
- Filtered streaming per subscriber
- Automatic buffer management
- Graceful degradation on overload

### EventReplay Component

**Purpose**: Historical event replay for debugging and analysis

**Class Design**:
```python
class EventReplay:
    """Event replay engine for historical analysis"""

    def __init__(self, store: EventStore):
        self.store = store
        self.replay_state = ReplayState()
        self.speed_controller = SpeedController()

    async def replay_from(
        self,
        start_time: datetime,
        filters: Optional[EventFilters] = None,
        speed: float = 1.0
    ) -> AsyncIterator[Event]:
        """Replay events from specific point"""

    async def replay_session(
        self,
        session_id: str,
        include_related: bool = True
    ) -> AsyncIterator[Event]:
        """Replay all events for a session"""

    def save_position(
        self,
        checkpoint_name: str
    ) -> None:
        """Save replay position for later resume"""

    def load_position(
        self,
        checkpoint_name: str
    ) -> ReplayState:
        """Load saved replay position"""
```

**Replay Features**:
- Variable speed playback
- Checkpoint/resume support
- Filtered replay
- Session reconstruction

### EventFilter Component

**Purpose**: Advanced filtering and query capabilities

**Class Design**:
```python
class EventFilter:
    """Event filtering and query engine"""

    def __init__(self):
        self.parser = FilterParser()
        self.optimizer = QueryOptimizer()

    def build_filter(
        self,
        type_pattern: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        source: Optional[str] = None,
        content_regex: Optional[str] = None
    ) -> EventFilters:
        """Build filter from parameters"""

    def parse_expression(
        self,
        expression: str
    ) -> EventFilters:
        """Parse filter expression string"""

    def match(
        self,
        event: Event,
        filters: EventFilters
    ) -> bool:
        """Check if event matches filters"""
```

**Filter Syntax**:
```python
# Time-based filtering
filter = "timestamp > '2024-01-20T10:00:00' AND timestamp < '2024-01-20T12:00:00'"

# Type filtering with wildcards
filter = "type LIKE 'pipeline.*' OR type = 'hook.executed'"

# Content search
filter = "payload.status = 'error' AND payload.message CONTAINS 'timeout'"

# Compound expressions
filter = "(type = 'synthesis' AND payload.duration > 1000) OR source = 'critical'"
```

### EventAnalyzer Component

**Purpose**: Event pattern detection and statistical analysis

**Class Design**:
```python
class EventAnalyzer:
    """Event analysis and pattern detection"""

    def __init__(self, store: EventStore):
        self.store = store
        self.pattern_detector = PatternDetector()
        self.stats_calculator = StatsCalculator()
        self.anomaly_detector = AnomalyDetector()

    async def analyze_patterns(
        self,
        time_window: timedelta,
        min_occurrence: int = 3
    ) -> List[EventPattern]:
        """Detect recurring event patterns"""

    async def calculate_statistics(
        self,
        event_type: str,
        time_range: Tuple[datetime, datetime]
    ) -> EventStatistics:
        """Calculate event statistics"""

    async def detect_anomalies(
        self,
        baseline_window: timedelta,
        sensitivity: float = 0.95
    ) -> List[Anomaly]:
        """Detect anomalous event patterns"""

    async def trace_event_chain(
        self,
        correlation_id: str
    ) -> EventChain:
        """Trace related events by correlation"""
```

**Analysis Outputs**:
```python
@dataclass
class EventStatistics:
    event_type: str
    count: int
    frequency: float  # events per minute
    avg_duration: Optional[float]
    percentiles: Dict[int, float]
    time_distribution: Dict[str, int]  # hourly buckets

@dataclass
class EventPattern:
    pattern_type: str
    events: List[Event]
    frequency: float
    confidence: float
    description: str
```

## Data Models

### Core Event Models

```python
@dataclass
class Event:
    """Core event data structure"""
    id: str
    timestamp: datetime
    type: str
    source: str
    correlation_id: Optional[str]
    payload: Dict[str, Any]
    metadata: EventMetadata

@dataclass
class EventMetadata:
    """Event metadata"""
    host: str
    version: str
    user: Optional[str]
    session_id: Optional[str]
    tags: List[str]

@dataclass
class EventFilters:
    """Event filter criteria"""
    type_patterns: List[str]
    time_range: Optional[Tuple[datetime, datetime]]
    sources: List[str]
    correlation_ids: List[str]
    content_patterns: List[Pattern]

@dataclass
class ReplayState:
    """Replay position tracking"""
    position: int
    timestamp: datetime
    filters: EventFilters
    speed: float
```

## Event Flow Architecture

### Logging Flow

```
1. Event Generation
   │
   ├─→ Event Creation
   │   ├─→ ID Generation
   │   ├─→ Timestamp Assignment
   │   └─→ Metadata Enrichment
   │
   ├─→ Buffering
   │   ├─→ Memory Buffer
   │   └─→ Overflow Handling
   │
   ├─→ Persistence
   │   ├─→ Append to Log
   │   ├─→ Index Update
   │   └─→ Rotation Check
   │
   └─→ Streaming
       ├─→ Subscriber Filtering
       ├─→ Queue Distribution
       └─→ Backpressure Management
```

### Query Processing Flow

```
1. Query Request
   │
   ├─→ Filter Parsing
   │   ├─→ Syntax Validation
   │   └─→ Optimization
   │
   ├─→ Index Lookup
   │   ├─→ Time Range Index
   │   └─→ Type Index
   │
   ├─→ Log Scanning
   │   ├─→ Filter Application
   │   └─→ Result Collection
   │
   └─→ Result Assembly
       ├─→ Sorting
       ├─→ Limiting
       └─→ Formatting
```

## Integration Points

### Internal Event Bus

```python
# Event emission interface
class EventBus:
    """Internal event distribution"""

    def emit(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Emit event to logger"""

    def on(
        self,
        event_type: str,
        handler: Callable
    ) -> None:
        """Register event handler"""
```

### Standard Event Types

```python
# Pipeline events
PIPELINE_EVENTS = {
    'pipeline.started': PipelineStartedEvent,
    'pipeline.stage.started': StageStartedEvent,
    'pipeline.stage.completed': StageCompletedEvent,
    'pipeline.completed': PipelineCompletedEvent,
    'pipeline.failed': PipelineFailedEvent
}

# Hook events
HOOK_EVENTS = {
    'hook.session.start': SessionStartHookEvent,
    'hook.session.stop': SessionStopHookEvent,
    'hook.tool.before': ToolBeforeHookEvent,
    'hook.tool.after': ToolAfterHookEvent,
    'hook.config.changed': ConfigChangedHookEvent
}

# Processing events
PROCESSING_EVENTS = {
    'process.document.started': DocumentStartedEvent,
    'process.extraction.completed': ExtractionCompletedEvent,
    'process.synthesis.completed': SynthesisCompletedEvent,
    'process.batch.progress': BatchProgressEvent,
    'process.retry.attempted': RetryAttemptedEvent
}
```

### External Dependencies

- `asyncio`: Async I/O operations
- `aiofiles`: Async file operations
- `orjson`: Fast JSON serialization
- No direct dependencies on other application modules

## Configuration

### Module Configuration

```yaml
events:
  logging:
    buffer_size: 10000
    flush_interval: 1.0  # seconds
    async_writes: true

  storage:
    base_path: ./data/events/
    rotation:
      max_size: 100MB
      max_age: 30  # days
      compress: true
    index:
      enabled: true
      rebuild_interval: 3600  # seconds
    retention:
      default: 90  # days
      by_type:
        error: 365
        audit: 2555  # 7 years

  streaming:
    max_subscribers: 100
    default_buffer_size: 1000
    backpressure_threshold: 0.8
    slow_consumer_timeout: 30  # seconds

  replay:
    max_speed: 100.0
    checkpoint_dir: ./data/events/checkpoints/
    session_cache_size: 1000

  analysis:
    pattern_window: 3600  # seconds
    anomaly_sensitivity: 0.95
    statistics_cache_ttl: 300  # seconds
```

## Performance Considerations

### Optimization Strategies

1. **Write Batching**: Buffer events for batch writes
2. **Async I/O**: Non-blocking file operations
3. **Index Caching**: Memory-cached indices for queries
4. **Stream Buffering**: Per-subscriber buffers
5. **Compression**: Automatic log compression

### Scalability Limits

- Event throughput: 10,000 events/second
- Concurrent subscribers: 100 streams
- Query response time: < 100ms for indexed queries
- Storage efficiency: 10:1 compression ratio
- Replay speed: Up to 100x real-time

## Testing Strategy

### Unit Tests

```python
class TestEventLogger:
    """Test event logging functionality"""

    def test_event_id_uniqueness(self):
        """Verify unique ID generation"""

    def test_timestamp_ordering(self):
        """Verify event timestamp ordering"""

    def test_correlation_tracking(self):
        """Test correlation ID propagation"""

class TestEventFilter:
    """Test filtering capabilities"""

    def test_expression_parsing(self):
        """Test filter expression parsing"""

    def test_compound_filters(self):
        """Test complex filter combinations"""

    def test_regex_matching(self):
        """Test content regex patterns"""
```

### Integration Tests

```python
class TestEventIntegration:
    """Test module integration"""

    async def test_log_stream_replay(self):
        """Test logging, streaming, and replay flow"""

    async def test_rotation_during_writes(self):
        """Test log rotation under load"""

    async def test_backpressure_handling(self):
        """Test slow consumer handling"""
```

## Error Handling

### Exception Hierarchy

```python
class EventException(Exception):
    """Base exception for event module"""

class EventStorageException(EventException):
    """Storage operation errors"""

class EventStreamException(EventException):
    """Streaming errors"""

class EventFilterException(EventException):
    """Filter/query errors"""

class EventAnalysisException(EventException):
    """Analysis errors"""
```

### Recovery Strategies

- **Storage Failures**: Fallback to memory buffer
- **Stream Overload**: Drop oldest events with notification
- **Index Corruption**: Rebuild from logs
- **Query Timeout**: Return partial results

## Security Considerations

### Access Control
- Event type-based permissions
- Read/write/admin roles
- Audit event protection
- Sensitive data masking

### Data Protection
- Encryption at rest for archived logs
- Secure event transmission
- PII detection and masking
- Compliance with retention policies

## Future Enhancements

### Planned Features
1. **Distributed Logging**: Multi-node event aggregation
2. **Real-time Dashboards**: WebSocket-based visualizations
3. **ML-based Analysis**: Predictive pattern detection
4. **Event Sourcing**: Full system state reconstruction
5. **External Integrations**: Export to monitoring systems

### Extension Points
- Custom event serializers
- Pluggable storage backends
- Additional export formats
- Custom analysis algorithms

## Module Contract

### Inputs
- Event data with type and payload
- Filter expressions for queries
- Configuration for behavior
- Correlation IDs for tracing

### Outputs
- Unique event IDs
- Query result sets
- Event streams
- Analysis reports
- Export files

### Side Effects
- Writes to `./data/events/` directory
- Creates index files
- Manages log rotation
- Compresses archived logs

### Guarantees
- Append-only event integrity
- Ordered event storage
- At-least-once delivery for streams
- Eventual consistency for indices
- Graceful degradation under load

## Usage Examples

### Basic Event Logging

```python
# Initialize logger
logger = EventLogger(config)

# Log simple event
event_id = logger.log(
    event_type="user.action",
    payload={"action": "login", "user_id": "123"},
    source="auth_module"
)

# Log with correlation
with logger.with_correlation("session_abc") as ctx_logger:
    ctx_logger.log("process.started", {"step": "validation"})
    ctx_logger.log("process.completed", {"step": "validation"})
```

### Event Streaming

```python
# Subscribe to events
streamer = EventStreamer()
subscriber = await streamer.subscribe(
    "my_subscriber",
    filters=EventFilter().build_filter(type_pattern="pipeline.*")
)

# Stream events
async for event in streamer.stream("my_subscriber"):
    print(f"Received: {event.type} at {event.timestamp}")
```

### Event Analysis

```python
# Analyze patterns
analyzer = EventAnalyzer(store)
patterns = await analyzer.analyze_patterns(
    time_window=timedelta(hours=1),
    min_occurrence=5
)

# Get statistics
stats = await analyzer.calculate_statistics(
    event_type="api.request",
    time_range=(start_time, end_time)
)
```

This Event Module provides a robust foundation for system observability, debugging, and audit trails while maintaining the modular "bricks and studs" philosophy with clear interfaces for integration with other system components.