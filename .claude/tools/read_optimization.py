#!/usr/bin/env python3
"""
Read Optimization Tool

Intelligent batch reading utilities that optimize Read tool usage through
context-aware prefetching, strategic batching, and memory efficiency patterns.
Addresses 144+ optimization opportunities identified in claude-trace analysis.
"""

import fnmatch
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReadOptimizationMetrics:
    """Metrics for tracking read optimization performance."""

    total_reads: int = 0
    batched_reads: int = 0
    cache_hits: int = 0
    execution_time: float = 0.0
    memory_usage: int = 0
    context_accuracy: float = 0.0

    def calculate_efficiency(self) -> Dict[str, float]:
        """Calculate optimization efficiency metrics."""
        if self.total_reads == 0:
            return {}

        return {
            "batch_ratio": self.batched_reads / self.total_reads,
            "cache_efficiency": self.cache_hits / self.total_reads,
            "avg_execution_time": self.execution_time / self.total_reads,
            "memory_per_read": self.memory_usage / self.total_reads,
            "context_accuracy": self.context_accuracy,
        }


@dataclass
class ReadContext:
    """Context information for optimizing read operations."""

    task_type: str  # architecture_analysis, feature_implementation, bug_investigation, etc.
    primary_files: List[str]
    related_patterns: List[str]
    exclude_patterns: List[str]
    max_depth: int = 2
    include_tests: bool = True
    include_docs: bool = True


class ReadOptimizer:
    """
    Intelligent batch reading system that optimizes Read tool usage through
    context-aware prefetching and strategic batching.
    """

    def __init__(self, cache_size: int = 1000):
        """Initialize the read optimizer with caching capability."""
        self.read_cache: Dict[str, Any] = {}
        self.context_graph: Dict[str, Set[str]] = defaultdict(set)
        self.metrics = ReadOptimizationMetrics()
        self.cache_size = cache_size
        self.file_patterns = {
            "python": ["*.py"],
            "javascript": ["*.js", "*.ts", "*.jsx", "*.tsx"],
            "config": ["*.json", "*.yaml", "*.yml", "*.toml", "*.ini"],
            "docs": ["*.md", "*.rst", "*.txt"],
            "tests": ["test_*.py", "*_test.py", "tests/**/*.py"],
            "workflows": [".github/workflows/*.yml", ".github/workflows/*.yaml"],
        }

    def clear_cache(self) -> None:
        """Clear the read cache and reset metrics."""
        self.read_cache.clear()
        self.context_graph.clear()
        self.metrics = ReadOptimizationMetrics()

    def predict_related_files(self, file_path: str, context: ReadContext) -> List[str]:
        """
        Predict related files based on imports, naming patterns, and context.

        Args:
            file_path: Primary file to analyze
            context: Read context with task type and patterns

        Returns:
            List of predicted related file paths
        """
        start_time = time.time()
        related_files = set()

        try:
            # Get file directory and name components
            path_obj = Path(file_path)
            file_dir = path_obj.parent
            file_stem = path_obj.stem
            file_suffix = path_obj.suffix

            # Pattern 1: Related files in same directory
            if file_suffix == ".py":
                related_files.update(self._find_python_related(file_path, file_dir, file_stem))
            elif file_suffix in [".js", ".ts", ".jsx", ".tsx"]:
                related_files.update(self._find_javascript_related(file_path, file_dir, file_stem))

            # Pattern 2: Task-specific patterns
            if context.task_type == "architecture_analysis":
                related_files.update(self._find_architecture_files(file_path))
            elif context.task_type == "feature_implementation":
                related_files.update(self._find_feature_files(file_path, context))
            elif context.task_type == "bug_investigation":
                related_files.update(self._find_debug_files(file_path))

            # Pattern 3: Include tests if requested
            if context.include_tests:
                related_files.update(self._find_test_files(file_path))

            # Pattern 4: Include documentation if requested
            if context.include_docs:
                related_files.update(self._find_doc_files(file_path))

            # Pattern 5: Apply custom patterns from context
            for pattern in context.related_patterns:
                related_files.update(self._glob_pattern(pattern))

            # Filter out excluded patterns
            filtered_files = self._filter_excluded(list(related_files), context.exclude_patterns)

            # Limit by max_depth
            final_files = self._limit_by_depth(filtered_files, file_path, context.max_depth)

            execution_time = time.time() - start_time
            logger.info(
                f"Predicted {len(final_files)} related files for {file_path} in {execution_time:.2f}s"
            )

            return final_files

        except Exception as e:
            logger.error(f"Error predicting related files for {file_path}: {e}")
            return []

    def _find_python_related(self, file_path: str, file_dir: Path, file_stem: str) -> Set[str]:
        """Find Python-specific related files."""
        related = set()

        # Same directory Python files
        for py_file in file_dir.glob("*.py"):
            if py_file.name != Path(file_path).name:
                related.add(str(py_file))

        # __init__.py files for package structure
        init_file = file_dir / "__init__.py"
        if init_file.exists():
            related.add(str(init_file))

        # Parent package __init__.py
        parent_init = file_dir.parent / "__init__.py"
        if parent_init.exists():
            related.add(str(parent_init))

        # Configuration files
        for config_pattern in ["config.py", "settings.py", "constants.py"]:
            config_file = file_dir / config_pattern
            if config_file.exists():
                related.add(str(config_file))

        return related

    def _find_javascript_related(self, file_path: str, file_dir: Path, file_stem: str) -> Set[str]:
        """Find JavaScript/TypeScript-specific related files."""
        related = set()

        # Same directory JS/TS files
        for js_pattern in ["*.js", "*.ts", "*.jsx", "*.tsx"]:
            for js_file in file_dir.glob(js_pattern):
                if js_file.name != Path(file_path).name:
                    related.add(str(js_file))

        # Index files
        for index_pattern in ["index.js", "index.ts", "index.jsx", "index.tsx"]:
            index_file = file_dir / index_pattern
            if index_file.exists():
                related.add(str(index_file))

        # Package.json and config files
        package_file = file_dir / "package.json"
        if package_file.exists():
            related.add(str(package_file))

        return related

    def _find_architecture_files(self, file_path: str) -> Set[str]:
        """Find architecture-related files."""
        related = set()

        # Common architecture files
        arch_patterns = [
            "**/__init__.py",
            "**/config.py",
            "**/settings.py",
            "**/models.py",
            "**/interfaces.py",
            "**/constants.py",
            "requirements*.txt",
            "pyproject.toml",
            "setup.py",
            "package.json",
        ]

        for pattern in arch_patterns:
            related.update(self._glob_pattern(pattern))

        return related

    def _find_feature_files(self, file_path: str, context: ReadContext) -> Set[str]:
        """Find feature implementation related files."""
        related = set()

        # Look for similar feature implementations
        path_obj = Path(file_path)
        file_stem = path_obj.stem

        # Find files with similar naming patterns
        for pattern in [f"*{file_stem}*", f"{file_stem}_*", f"*_{file_stem}"]:
            related.update(self._glob_pattern(f"**/{pattern}.py"))

        # Common feature files
        feature_patterns = [
            "**/models.py",
            "**/views.py",
            "**/routes.py",
            "**/handlers.py",
            "**/middleware.py",
            "**/utils.py",
            "**/helpers.py",
        ]

        for pattern in feature_patterns:
            related.update(self._glob_pattern(pattern))

        return related

    def _find_debug_files(self, file_path: str) -> Set[str]:
        """Find debugging-related files."""
        related = set()

        # Error handling and logging files
        debug_patterns = [
            "**/exceptions.py",
            "**/errors.py",
            "**/logging.py",
            "**/retry.py",
            "**/health*.py",
            "**/*error*.py",
            "**/*exception*.py",
        ]

        for pattern in debug_patterns:
            related.update(self._glob_pattern(pattern))

        # Log files
        log_patterns = ["**/*.log", "**/logs/**/*"]
        for pattern in log_patterns:
            related.update(self._glob_pattern(pattern))

        return related

    def _find_test_files(self, file_path: str) -> Set[str]:
        """Find test files related to the given file."""
        related = set()

        path_obj = Path(file_path)
        file_stem = path_obj.stem

        # Test file patterns
        test_patterns = [
            f"**/test_{file_stem}.py",
            f"**/{file_stem}_test.py",
            f"**/test_*{file_stem}*.py",
            f"**/tests/*{file_stem}*.py",
            "**/conftest.py",
            "**/test_*.py",
        ]

        for pattern in test_patterns:
            related.update(self._glob_pattern(pattern))

        return related

    def _find_doc_files(self, file_path: str) -> Set[str]:
        """Find documentation files related to the given file."""
        related = set()

        path_obj = Path(file_path)
        file_stem = path_obj.stem

        # Documentation patterns
        doc_patterns = [
            f"**/{file_stem}.md",
            f"**/docs/*{file_stem}*.md",
            "**/README*.md",
            "**/CHANGELOG*.md",
            "**/*.rst",
        ]

        for pattern in doc_patterns:
            related.update(self._glob_pattern(pattern))

        return related

    def _glob_pattern(self, pattern: str) -> Set[str]:
        """Safely execute glob pattern and return matching files."""
        try:
            # Use pathlib for safe globbing
            if pattern.startswith("**/"):
                # Recursive pattern
                matches = Path(".").rglob(pattern[3:])
            else:
                # Non-recursive pattern
                matches = Path(".").glob(pattern)

            return {str(match) for match in matches if match.is_file()}
        except Exception as e:
            logger.warning(f"Error in glob pattern '{pattern}': {e}")
            return set()

    def _filter_excluded(self, files: List[str], exclude_patterns: List[str]) -> List[str]:
        """Filter out files matching exclude patterns."""
        if not exclude_patterns:
            return files

        filtered = []
        for file_path in files:
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    excluded = True
                    break
            if not excluded:
                filtered.append(file_path)

        return filtered

    def _limit_by_depth(self, files: List[str], primary_file: str, max_depth: int) -> List[str]:
        """Limit files by directory depth from primary file."""
        if max_depth <= 0:
            return files

        primary_depth = len(Path(primary_file).parts)
        filtered = []

        for file_path in files:
            file_depth = len(Path(file_path).parts)
            if abs(file_depth - primary_depth) <= max_depth:
                filtered.append(file_path)

        return filtered

    def create_batch_groups(self, files: List[str], max_batch_size: int = 10) -> List[List[str]]:
        """
        Create optimal batch groups for reading files.

        Args:
            files: List of file paths to batch
            max_batch_size: Maximum files per batch

        Returns:
            List of batches, each containing a list of file paths
        """
        if not files:
            return []

        # Sort files by priority (size, type, etc.)
        prioritized_files = self._prioritize_files(files)

        # Create batches
        batches = []
        current_batch = []

        for file_path in prioritized_files:
            current_batch.append(file_path)

            if len(current_batch) >= max_batch_size:
                batches.append(current_batch)
                current_batch = []

        # Add remaining files as final batch
        if current_batch:
            batches.append(current_batch)

        logger.info(f"Created {len(batches)} batches from {len(files)} files")
        return batches

    def _prioritize_files(self, files: List[str]) -> List[str]:
        """Prioritize files for optimal reading order."""
        prioritized = []

        # Group files by type and priority
        config_files = []
        interface_files = []
        implementation_files = []
        test_files = []
        doc_files = []
        other_files = []

        for file_path in files:
            if self._is_config_file(file_path):
                config_files.append(file_path)
            elif self._is_interface_file(file_path):
                interface_files.append(file_path)
            elif self._is_test_file(file_path):
                test_files.append(file_path)
            elif self._is_doc_file(file_path):
                doc_files.append(file_path)
            elif self._is_implementation_file(file_path):
                implementation_files.append(file_path)
            else:
                other_files.append(file_path)

        # Order by priority: config → interfaces → implementation → tests → docs → other
        prioritized.extend(sorted(config_files))
        prioritized.extend(sorted(interface_files))
        prioritized.extend(sorted(implementation_files))
        prioritized.extend(sorted(test_files))
        prioritized.extend(sorted(doc_files))
        prioritized.extend(sorted(other_files))

        return prioritized

    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        config_patterns = [
            "*config*",
            "*settings*",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.toml",
            "*.ini",
            "requirements*",
            "pyproject.toml",
            "package.json",
            "Dockerfile",
            "docker-compose*",
        ]
        return any(fnmatch.fnmatch(file_path.lower(), pattern) for pattern in config_patterns)

    def _is_interface_file(self, file_path: str) -> bool:
        """Check if file is an interface file."""
        return (
            file_path.endswith("__init__.py")
            or "interface" in file_path.lower()
            or "api" in file_path.lower()
        )

    def _is_implementation_file(self, file_path: str) -> bool:
        """Check if file is an implementation file."""
        return (
            file_path.endswith((".py", ".js", ".ts", ".jsx", ".tsx"))
            and not self._is_test_file(file_path)
            and not self._is_config_file(file_path)
            and not self._is_interface_file(file_path)
        )

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        test_patterns = ["test_*", "*_test.*", "tests/**/*", "**/test/**/*"]
        return any(fnmatch.fnmatch(file_path.lower(), pattern) for pattern in test_patterns)

    def _is_doc_file(self, file_path: str) -> bool:
        """Check if file is a documentation file."""
        return file_path.endswith((".md", ".rst", ".txt"))

    def optimize_read_sequence(self, context: ReadContext) -> Dict[str, Any]:
        """
        Optimize a reading sequence based on context.

        Args:
            context: Read context with task type and file patterns

        Returns:
            Dictionary with optimized reading plan
        """
        start_time = time.time()

        try:
            # Start with primary files
            all_files = set(context.primary_files)

            # Predict related files for each primary file
            for primary_file in context.primary_files:
                related = self.predict_related_files(primary_file, context)
                all_files.update(related)

            # Convert to list and remove duplicates
            unique_files = list(all_files)

            # Create optimal batch groups
            batch_groups = self.create_batch_groups(unique_files)

            # Update metrics
            self.metrics.total_reads += len(unique_files)
            self.metrics.batched_reads += len(unique_files)
            execution_time = time.time() - start_time
            self.metrics.execution_time += execution_time

            optimization_plan = {
                "task_type": context.task_type,
                "total_files": len(unique_files),
                "batch_groups": batch_groups,
                "optimization_ratio": len(batch_groups) / len(unique_files) if unique_files else 0,
                "execution_time": execution_time,
                "recommendations": self._generate_recommendations(context, batch_groups),
            }

            logger.info(
                f"Optimized read sequence: {len(unique_files)} files in {len(batch_groups)} batches"
            )
            return optimization_plan

        except Exception as e:
            logger.error(f"Error optimizing read sequence: {e}")
            return {"error": str(e)}

    def _generate_recommendations(
        self, context: ReadContext, batch_groups: List[List[str]]
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if len(batch_groups) > 5:
            recommendations.append(
                f"Consider increasing max_batch_size to reduce {len(batch_groups)} batches"
            )

        if context.task_type == "architecture_analysis" and not context.include_docs:
            recommendations.append(
                "Consider including documentation files for better architecture understanding"
            )

        if context.task_type == "feature_implementation" and not context.include_tests:
            recommendations.append(
                "Consider including test files to understand implementation patterns"
            )

        total_files = sum(len(batch) for batch in batch_groups)
        if total_files > 50:
            recommendations.append(
                "Large file count detected - consider adding more specific exclude patterns"
            )

        return recommendations

    def cache_read_result(self, file_path: str, content: Any) -> None:
        """Cache read result for future use."""
        # Implement LRU-style cache with size limit
        if len(self.read_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self.read_cache))
            del self.read_cache[oldest_key]

        self.read_cache[file_path] = {
            "content": content,
            "timestamp": time.time(),
            "hash": self._content_hash(content),
        }

    def get_cached_result(self, file_path: str) -> Optional[Any]:
        """Get cached read result if available."""
        if file_path in self.read_cache:
            self.metrics.cache_hits += 1
            return self.read_cache[file_path]["content"]
        return None

    def _content_hash(self, content: Any) -> str:
        """Generate hash for content comparison."""
        try:
            content_str = str(content)
            return hashlib.md5(content_str.encode()).hexdigest()
        except Exception:
            return ""

    def generate_metrics_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        efficiency = self.metrics.calculate_efficiency()

        report = {
            "metrics": {
                "total_reads": self.metrics.total_reads,
                "batched_reads": self.metrics.batched_reads,
                "cache_hits": self.metrics.cache_hits,
                "execution_time": self.metrics.execution_time,
                "memory_usage": self.metrics.memory_usage,
            },
            "efficiency": efficiency,
            "performance_targets": {
                "batch_ratio_target": 0.8,
                "cache_efficiency_target": 0.6,
                "context_accuracy_target": 0.9,
            },
            "recommendations": self._generate_performance_recommendations(efficiency),
        }

        return report

    def _generate_performance_recommendations(self, efficiency: Dict[str, float]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if efficiency.get("batch_ratio", 0) < 0.8:
            recommendations.append(
                "Batch ratio below target (80%) - consider larger batch sizes or better grouping"
            )

        if efficiency.get("cache_efficiency", 0) < 0.6:
            recommendations.append(
                "Cache efficiency below target (60%) - files may not be reused enough"
            )

        if efficiency.get("context_accuracy", 0) < 0.9:
            recommendations.append(
                "Context accuracy below target (90%) - improve related file prediction"
            )

        if not recommendations:
            recommendations.append("Performance targets met - system operating optimally")

        return recommendations


# Convenience functions for common use cases


def optimize_architecture_analysis(primary_files: List[str], **kwargs) -> Dict[str, Any]:
    """Optimize reading for architecture analysis tasks."""
    context = ReadContext(
        task_type="architecture_analysis",
        primary_files=primary_files,
        related_patterns=kwargs.get("related_patterns", ["**/__init__.py", "**/config.py"]),
        exclude_patterns=kwargs.get("exclude_patterns", ["**/__pycache__/**", "**/.git/**"]),
        include_tests=kwargs.get("include_tests", True),
        include_docs=kwargs.get("include_docs", True),
    )

    optimizer = ReadOptimizer()
    return optimizer.optimize_read_sequence(context)


def optimize_feature_implementation(primary_files: List[str], **kwargs) -> Dict[str, Any]:
    """Optimize reading for feature implementation tasks."""
    context = ReadContext(
        task_type="feature_implementation",
        primary_files=primary_files,
        related_patterns=kwargs.get("related_patterns", ["**/models.py", "**/views.py"]),
        exclude_patterns=kwargs.get("exclude_patterns", ["**/__pycache__/**", "**/.git/**"]),
        include_tests=kwargs.get("include_tests", True),
        include_docs=kwargs.get("include_docs", False),
    )

    optimizer = ReadOptimizer()
    return optimizer.optimize_read_sequence(context)


def optimize_bug_investigation(primary_files: List[str], **kwargs) -> Dict[str, Any]:
    """Optimize reading for bug investigation tasks."""
    context = ReadContext(
        task_type="bug_investigation",
        primary_files=primary_files,
        related_patterns=kwargs.get("related_patterns", ["**/*error*.py", "**/*exception*.py"]),
        exclude_patterns=kwargs.get("exclude_patterns", ["**/__pycache__/**", "**/.git/**"]),
        include_tests=kwargs.get("include_tests", True),
        include_docs=kwargs.get("include_docs", False),
    )

    optimizer = ReadOptimizer()
    return optimizer.optimize_read_sequence(context)


if __name__ == "__main__":
    # Example usage and testing
    import argparse

    parser = argparse.ArgumentParser(description="Read Optimization Tool")
    parser.add_argument(
        "--task-type",
        choices=["architecture", "feature", "debug"],
        default="architecture",
        help="Type of optimization task",
    )
    parser.add_argument("--files", nargs="+", required=True, help="Primary files to analyze")
    parser.add_argument("--max-batch-size", type=int, default=10, help="Maximum batch size")
    parser.add_argument("--exclude", nargs="*", default=[], help="Exclude patterns")

    args = parser.parse_args()

    # Create context based on task type
    if args.task_type == "architecture":
        result = optimize_architecture_analysis(args.files, exclude_patterns=args.exclude)
    elif args.task_type == "feature":
        result = optimize_feature_implementation(args.files, exclude_patterns=args.exclude)
    else:
        result = optimize_bug_investigation(args.files, exclude_patterns=args.exclude)

    print(json.dumps(result, indent=2))
