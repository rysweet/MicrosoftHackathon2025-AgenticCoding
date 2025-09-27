"""Core modules for claude-trace analysis system.

Contains the five main components:
- jsonl_parser: Pure JSONL parsing with validation
- pattern_extractor: Analysis with specialized analyzers
- deduplication_engine: Multi-layer duplicate prevention
- issue_generator: GitHub integration with templates
- orchestrator: Main coordination logic
"""

from .deduplication_engine import DeduplicationEngine
from .issue_generator import IssueGenerator
from .jsonl_parser import JSONLParser
from .orchestrator import TraceAnalyzer
from .pattern_extractor import PatternExtractor

__all__ = [
    "JSONLParser",
    "PatternExtractor",
    "DeduplicationEngine",
    "IssueGenerator",
    "TraceAnalyzer",
]
