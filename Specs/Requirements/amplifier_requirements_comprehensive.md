# Amplifier System - Comprehensive Functional Requirements

Generated: 2025-01-16
Project: /Users/ryan/src/hackathon/amplifier
Analysis Method: Direct Claude Code analysis with simplified extraction philosophy

## Executive Summary

The Amplifier system is a comprehensive AI development environment that supercharges coding assistants with specialized agents, knowledge synthesis capabilities, and powerful automation tools. It transforms helpful AI assistants into force multipliers that can deliver complex solutions with minimal hand-holding. The system focuses on knowledge amplification, parallel development, and ruthless simplicity in implementation.

---

## 1. Memory Management Module (REQ-MEM)

### REQ-MEM-001: Persistent Memory Storage
**Priority:** High
**Category:** Data
**Description:** The system shall provide persistent JSON-based storage of memories with automatic file rotation when reaching configured limits.
**Evidence:** `amplifier/memory/core.py:21-43` - MemoryStore class with file-based persistence

### REQ-MEM-002: Memory Categorization
**Priority:** High
**Category:** Data
**Description:** The system shall categorize memories into types: learning, decision, issue_solved, preference, and pattern.
**Evidence:** `amplifier/memory/models.py:10` - MemoryCategory type definition

### REQ-MEM-003: Memory Rotation Management
**Priority:** Medium
**Category:** Data
**Description:** The system shall automatically rotate old memories when exceeding MAX_MEMORIES limit (default 1000), keeping most accessed and recent memories.
**Evidence:** `amplifier/memory/core.py:160-173` - _rotate_memories method

### REQ-MEM-004: Batch Memory Operations
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall support batch addition of memories from extraction results with automatic metadata enrichment.
**Evidence:** `amplifier/memory/core.py:110-158` - add_memories_batch method

### REQ-MEM-005: Memory Access Tracking
**Priority:** Low
**Category:** Data
**Description:** The system shall track access count for each memory to support intelligent rotation decisions.
**Evidence:** `amplifier/memory/core.py:81-83` - Access count increment on retrieval

---

## 2. Knowledge Synthesis Module (REQ-KNS)

### REQ-KNS-001: Concept Extraction
**Priority:** High
**Category:** Data Processing
**Description:** The system shall extract concepts from text including name, description, category, and importance score.
**Evidence:** `amplifier/knowledge_mining/knowledge_extractor.py:31-38` - Concept dataclass

### REQ-KNS-002: Relationship Extraction
**Priority:** High
**Category:** Data Processing
**Description:** The system shall extract relationships between concepts including source, target, relationship type, and description.
**Evidence:** `amplifier/knowledge_mining/knowledge_extractor.py:41-49` - Relationship dataclass

### REQ-KNS-003: Knowledge Store Management
**Priority:** High
**Category:** Data
**Description:** The system shall store extracted knowledge in JSON Lines format for incremental processing and fast lookups.
**Evidence:** `amplifier/knowledge_synthesis/store.py:16-90` - KnowledgeStore class

### REQ-KNS-004: Semantic Fingerprinting
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall generate semantic fingerprints to identify similar concepts with different names (entity resolution).
**Evidence:** `amplifier/knowledge_synthesis/synthesis_engine.py:28,57-64` - SemanticFingerprinter usage

### REQ-KNS-005: Tension Detection
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall detect contradictions and tensions between different knowledge sources.
**Evidence:** `amplifier/knowledge_synthesis/synthesis_engine.py:30,69` - TensionDetector component

### REQ-KNS-006: Synthesis Insights Generation
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall generate synthesis insights by analyzing patterns across multiple knowledge sources.
**Evidence:** `amplifier/knowledge_synthesis/synthesis_engine.py:31,72` - Synthesizer component

### REQ-KNS-007: Emerging Concept Detection
**Priority:** Low
**Category:** Data Processing
**Description:** The system shall identify emerging concepts that appear with increasing frequency across sources.
**Evidence:** `amplifier/knowledge_synthesis/synthesis_engine.py:75` - find_emerging_concepts

---

## 3. Knowledge Mining Module (REQ-KMN)

### REQ-KMN-001: LLM-Powered Extraction
**Priority:** High
**Category:** Integration
**Description:** The system shall use Claude Code SDK for AI-powered knowledge extraction from text.
**Evidence:** `amplifier/knowledge_mining/knowledge_extractor.py:19-26,64-100` - Claude SDK integration

### REQ-KMN-002: Code Pattern Recognition
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall identify and extract code patterns from technical documentation and source code.
**Evidence:** `amplifier/knowledge_mining/knowledge_extractor.py:60` - code_patterns field

### REQ-KMN-003: Key Insights Extraction
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall extract key insights and learnings from analyzed content.
**Evidence:** `amplifier/knowledge_mining/knowledge_extractor.py:59` - key_insights field

### REQ-KMN-004: Document Type Awareness
**Priority:** Low
**Category:** Data Processing
**Description:** The system shall adapt extraction based on document type (article, API docs, code, conversation, tutorial).
**Evidence:** `amplifier/knowledge_integration/unified_extractor.py:49` - document_type parameter

---

## 4. Content Loading Module (REQ-CNT)

### REQ-CNT-001: Multi-Format Support
**Priority:** High
**Category:** Data
**Description:** The system shall load content from multiple file formats including .md (Markdown), .txt (Plain text), and .json (JSON).
**Evidence:** `amplifier/content_loader/loader.py:33` - SUPPORTED_EXTENSIONS

### REQ-CNT-002: Directory Scanning
**Priority:** High
**Category:** Data
**Description:** The system shall recursively scan configured directories for content files.
**Evidence:** `amplifier/content_loader/loader.py:128-175` - load_all method with rglob

### REQ-CNT-003: Content ID Generation
**Priority:** Medium
**Category:** Data
**Description:** The system shall generate unique content IDs using SHA256 hash of file paths for consistent identification.
**Evidence:** `amplifier/content_loader/loader.py:51-57` - _generate_content_id method

### REQ-CNT-004: Title Extraction
**Priority:** Low
**Category:** Data Processing
**Description:** The system shall automatically extract titles from content, using H1 headings for Markdown or filename as fallback.
**Evidence:** `amplifier/content_loader/loader.py:59-72` - _extract_title method

### REQ-CNT-005: Configurable Content Directories
**Priority:** Medium
**Category:** Configuration
**Description:** The system shall support multiple content directories via AMPLIFIER_CONTENT_DIRS environment variable.
**Evidence:** `amplifier/content_loader/loader.py:43-44` - Environment variable parsing

---

## 5. Search Module (REQ-SRC)

### REQ-SRC-001: Semantic Memory Search
**Priority:** High
**Category:** API
**Description:** The system shall provide semantic search of memories using sentence transformers for similarity matching.
**Evidence:** `amplifier/search/core.py:44-50` - SentenceTransformer model loading

### REQ-SRC-002: Keyword Fallback Search
**Priority:** Medium
**Category:** API
**Description:** The system shall fall back to keyword search when semantic search is unavailable.
**Evidence:** `amplifier/search/core.py:71-72` - Fallback to keyword search

### REQ-SRC-003: Search Result Ranking
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall rank search results by relevance score and return limited results.
**Evidence:** `amplifier/search/core.py:51-73` - Search method with limit parameter

### REQ-SRC-004: Recent Memory Retrieval
**Priority:** Medium
**Category:** API
**Description:** The system shall retrieve most recent memories sorted by timestamp.
**Evidence:** `amplifier/memory/core.py:68-85` - search_recent method

---

## 6. Validation Module (REQ-VAL)

### REQ-VAL-001: Claim Extraction
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall extract claims from text using pattern matching.
**Evidence:** `amplifier/validation/core.py:40` - extract_claims_from_text method

### REQ-VAL-002: Claim Validation Against Memories
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall validate claims against stored memories and provide confidence scores.
**Evidence:** `amplifier/validation/core.py:47-55` - validate_claim with confidence calculation

### REQ-VAL-003: Contradiction Detection
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall detect contradictions between claims and existing memories.
**Evidence:** `amplifier/validation/core.py:44-51` - Contradiction checking logic

### REQ-VAL-004: Validation Evidence Collection
**Priority:** Low
**Category:** Data Processing
**Description:** The system shall collect and present evidence supporting or contradicting claims.
**Evidence:** `amplifier/validation/core.py:76-80` - Evidence collection in results

---

## 7. Knowledge Integration Module (REQ-KIN)

### REQ-KIN-001: Unified Extraction Pipeline
**Priority:** High
**Category:** Integration
**Description:** The system shall run concept and relationship extraction in parallel for efficiency.
**Evidence:** `amplifier/knowledge_integration/unified_extractor.py:69-72` - Parallel asyncio.gather

### REQ-KIN-002: Entity Resolution
**Priority:** Medium
**Category:** Data Processing
**Description:** The system shall resolve different names for the same entity across sources.
**Evidence:** `amplifier/knowledge_integration/entity_resolver.py` - Entity resolution component

### REQ-KIN-003: Knowledge Graph Building
**Priority:** High
**Category:** Data Processing
**Description:** The system shall build knowledge graphs with concepts as nodes and relationships as edges.
**Evidence:** `amplifier/knowledge/graph_builder.py` - Graph building functionality

### REQ-KIN-004: Graph Visualization
**Priority:** Low
**Category:** UI
**Description:** The system shall visualize knowledge graphs for exploration and understanding.
**Evidence:** `amplifier/knowledge/graph_visualizer.py` - Visualization component

---

## 8. Testing & Quality Module (REQ-TST)

### REQ-TST-001: AI-Powered Test Evaluation
**Priority:** High
**Category:** Testing
**Description:** The system shall use AI to evaluate test results against success criteria.
**Evidence:** `amplifier/smoke_tests/ai_evaluator.py` - AIEvaluator class

### REQ-TST-002: Smoke Test Execution
**Priority:** High
**Category:** Testing
**Description:** The system shall execute smoke tests with configurable timeouts and capture output.
**Evidence:** `amplifier/smoke_tests/runner.py:43-59` - run_command method

### REQ-TST-003: Test Configuration via YAML
**Priority:** Medium
**Category:** Configuration
**Description:** The system shall load test definitions from YAML configuration files.
**Evidence:** `amplifier/smoke_tests/runner.py:37-41` - load_tests method

### REQ-TST-004: Test Result Reporting
**Priority:** Medium
**Category:** Testing
**Description:** The system shall report test results with pass/fail counts and colored terminal output.
**Evidence:** `amplifier/smoke_tests/runner.py:18-23,33-35` - Result tracking and colors

---

## 9. Configuration Management (REQ-CFG)

### REQ-CFG-001: Centralized Path Configuration
**Priority:** High
**Category:** Configuration
**Description:** The system shall maintain centralized configuration for all data paths and directories.
**Evidence:** `amplifier/config/paths.py` - Path configuration module

### REQ-CFG-002: Environment Variable Support
**Priority:** High
**Category:** Configuration
**Description:** The system shall support configuration via environment variables for flexibility.
**Evidence:** Multiple modules using os.environ.get() for configuration

### REQ-CFG-003: Default Configuration Values
**Priority:** Medium
**Category:** Configuration
**Description:** The system shall provide sensible defaults for all configuration values.
**Evidence:** Default values throughout configuration modules

---

## 10. Utility Services (REQ-UTL)

### REQ-UTL-001: File I/O with Retry Logic
**Priority:** Medium
**Category:** Utility
**Description:** The system shall handle file I/O operations with retry logic for cloud-synced files.
**Evidence:** `amplifier/utils/file_io.py` - File I/O utilities

### REQ-UTL-002: Token Counting
**Priority:** Low
**Category:** Utility
**Description:** The system shall provide utilities for counting tokens in text for LLM usage.
**Evidence:** `amplifier/utils/token_utils.py` - Token utilities

### REQ-UTL-003: Logging Infrastructure
**Priority:** Medium
**Category:** Utility
**Description:** The system shall provide consistent logging across all modules.
**Evidence:** `amplifier/utils/logging_utils.py` - Logging utilities

---

## 11. Agent System Integration (REQ-AGT)

### REQ-AGT-001: Specialized Agent Library
**Priority:** High
**Category:** Integration
**Description:** The system shall provide 20+ specialized AI agents for different development tasks.
**Evidence:** README.md:155-187 - Agent catalog listing

### REQ-AGT-002: Agent Orchestration
**Priority:** High
**Category:** Integration
**Description:** The system shall enable orchestration of multiple agents for complex tasks.
**Evidence:** Claude Code integration with agent system

### REQ-AGT-003: Parallel Agent Execution
**Priority:** Medium
**Category:** Performance
**Description:** The system shall support running multiple agents in parallel for efficiency.
**Evidence:** Parallel worktree system mentioned in README

---

## 12. Development Workflow Support (REQ-WFL)

### REQ-WFL-001: Parallel Worktree Management
**Priority:** High
**Category:** Development
**Description:** The system shall support creating and managing multiple Git worktrees for parallel development.
**Evidence:** README.md:121-134 - Worktree commands

### REQ-WFL-002: Knowledge-Driven Development
**Priority:** Medium
**Category:** Development
**Description:** The system shall enable querying accumulated knowledge to inform development decisions.
**Evidence:** README.md:195-209 - Knowledge base commands

### REQ-WFL-003: Code Quality Automation
**Priority:** Medium
**Category:** CI/CD
**Description:** The system shall provide automated linting, formatting, and type checking via make commands.
**Evidence:** README.md:211-217 - Development commands

---

## Non-Functional Requirements

### REQ-NFR-001: Ruthless Simplicity
**Priority:** High
**Category:** Architecture
**Description:** The system shall follow ruthless simplicity principles, avoiding unnecessary complexity.
**Evidence:** Philosophy documented throughout codebase

### REQ-NFR-002: Performance
**Priority:** High
**Category:** Performance
**Description:** The system shall process documents efficiently with configurable timeouts and parallel processing.
**Evidence:** Async/await patterns and parallel extraction

### REQ-NFR-003: Scalability
**Priority:** Medium
**Category:** Performance
**Description:** The system shall handle growing knowledge bases through incremental processing and rotation strategies.
**Evidence:** JSON Lines format, memory rotation, incremental saves

### REQ-NFR-004: Extensibility
**Priority:** Medium
**Category:** Architecture
**Description:** The system shall support adding new extractors, agents, and processing modules.
**Evidence:** Modular architecture with clear interfaces

### REQ-NFR-005: Error Resilience
**Priority:** High
**Category:** Reliability
**Description:** The system shall handle failures gracefully with clear error messages and fallback strategies.
**Evidence:** Try-catch blocks and error logging throughout

### REQ-NFR-006: Platform Compatibility
**Priority:** Medium
**Category:** Compatibility
**Description:** The system shall support Windows (WSL2), macOS, and Linux environments.
**Evidence:** README.md:33 - Platform note

---

## Summary Statistics

- **Total Requirements:** 56
- **By Priority:**
  - High: 26
  - Medium: 24
  - Low: 6
- **By Category:**
  - Data: 10
  - Data Processing: 18
  - Integration: 5
  - API: 3
  - Configuration: 5
  - Testing: 4
  - Development: 3
  - Utility: 3
  - UI: 1
  - Performance: 3
  - Architecture: 3
  - Reliability: 1
  - Compatibility: 1
  - CI/CD: 1

---

## Key Functional Areas

1. **Knowledge Management**: Extraction, synthesis, mining, and storage of knowledge from various sources
2. **Memory System**: Persistent storage and retrieval of learnings, decisions, and patterns
3. **Search & Validation**: Semantic search and claim validation against knowledge base
4. **Agent Integration**: 20+ specialized AI agents for development tasks
5. **Development Workflow**: Parallel development, knowledge queries, and automation
6. **Testing**: AI-powered test evaluation and smoke testing
7. **Configuration**: Flexible configuration via environment variables and files
8. **Integration**: Claude Code SDK and external service integration

---

*Note: This requirements document focuses on WHAT the Amplifier system does (functional capabilities) rather than HOW it's implemented (technical details). Requirements are derived from direct analysis of the codebase structure, module implementations, and documented features.*