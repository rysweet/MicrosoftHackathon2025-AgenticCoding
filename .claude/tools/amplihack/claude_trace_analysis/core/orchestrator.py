"""Main workflow orchestrator for claude-trace analysis system.

This module coordinates the entire analysis workflow:
1. Parse claude-trace JSONL files
2. Extract improvement patterns
3. Check for duplicates
4. Generate GitHub issues
5. Track and report results

Provides the main entry point for the claude-trace analysis system.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .deduplication_engine import DeduplicationEngine
from .issue_generator import IssueCreationResult, IssueGenerator
from .jsonl_parser import JSONLParser, ParsedEntry, ValidationError
from .pattern_extractor import ImprovementPattern, PatternExtractor


@dataclass
class AnalysisResult:
    """Result of complete claude-trace analysis.

    Attributes:
        success: Whether analysis completed successfully
        files_processed: Number of files processed
        entries_parsed: Number of entries parsed
        patterns_identified: Number of improvement patterns found
        unique_patterns: Number of unique patterns (after deduplication)
        issues_created: Number of GitHub issues created
        execution_time_seconds: Total execution time
        error_message: Error description if failed
        detailed_results: Detailed results by component
    """

    success: bool
    files_processed: int = 0
    entries_parsed: int = 0
    patterns_identified: int = 0
    unique_patterns: int = 0
    issues_created: int = 0
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    detailed_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary representation of the result
        """
        return {
            "success": self.success,
            "summary": {
                "files_processed": self.files_processed,
                "entries_parsed": self.entries_parsed,
                "patterns_identified": self.patterns_identified,
                "unique_patterns": self.unique_patterns,
                "issues_created": self.issues_created,
                "execution_time_seconds": self.execution_time_seconds,
            },
            "error_message": self.error_message,
            "detailed_results": self.detailed_results,
        }


class TraceAnalyzer:
    """Main orchestrator for claude-trace analysis workflow.

    Coordinates all components to provide end-to-end analysis:
    - JSONL parsing with security validation
    - Pattern extraction with specialized analyzers
    - Deduplication with multi-layer checking
    - GitHub issue generation with templates
    - Comprehensive result reporting
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        repo_owner: str = "",
        repo_name: str = "",
        daily_issue_limit: int = 50,
        hourly_issue_limit: int = 10,
    ):
        """Initialize trace analyzer.

        Args:
            github_token: GitHub API token for issue creation
            repo_owner: Repository owner for GitHub issues
            repo_name: Repository name for GitHub issues
            daily_issue_limit: Maximum GitHub issues per day
            hourly_issue_limit: Maximum GitHub issues per hour
        """
        # Initialize components
        self.parser = JSONLParser()
        self.pattern_extractor = PatternExtractor()
        self.deduplication_engine = DeduplicationEngine(
            github_token=github_token, repo_owner=repo_owner, repo_name=repo_name
        )
        self.issue_generator = IssueGenerator(
            github_token=github_token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            daily_limit=daily_issue_limit,
            hourly_limit=hourly_issue_limit,
        )

        # Configuration
        self.github_integration_enabled = bool(github_token and repo_owner and repo_name)

        # Runtime state
        self.last_analysis_result: Optional[AnalysisResult] = None

    def analyze_trace_files(
        self, file_paths: List[str], create_issues: bool = True
    ) -> AnalysisResult:
        """Analyze claude-trace files and optionally create GitHub issues.

        Args:
            file_paths: List of claude-trace JSONL file paths
            create_issues: Whether to create GitHub issues for patterns

        Returns:
            AnalysisResult with comprehensive analysis results
        """
        start_time = time.time()

        try:
            # Step 1: Parse all JSONL files
            all_entries = self._parse_files(file_paths)
            if not all_entries:
                return AnalysisResult(
                    success=False,
                    error_message="No valid entries found in trace files",
                    execution_time_seconds=time.time() - start_time,
                )

            # Step 2: Extract improvement patterns
            patterns = self._extract_patterns(all_entries)
            if not patterns:
                return AnalysisResult(
                    success=True,
                    files_processed=len(file_paths),
                    entries_parsed=len(all_entries),
                    patterns_identified=0,
                    execution_time_seconds=time.time() - start_time,
                    detailed_results={"message": "No improvement patterns detected in trace files"},
                )

            # Step 3: Deduplicate patterns
            unique_patterns = self._deduplicate_patterns(patterns)

            # Step 4: Create GitHub issues (if enabled and requested)
            issues_created: int = 0
            issue_results: List[IssueCreationResult] = []
            if create_issues and self.github_integration_enabled:
                issues_created, issue_results = self._create_issues(unique_patterns)
            elif create_issues and not self.github_integration_enabled:
                # Log that GitHub integration is not available
                pass

            # Step 5: Compile comprehensive results
            execution_time = time.time() - start_time

            result = AnalysisResult(
                success=True,
                files_processed=len(file_paths),
                entries_parsed=len(all_entries),
                patterns_identified=len(patterns),
                unique_patterns=len(unique_patterns),
                issues_created=issues_created,
                execution_time_seconds=execution_time,
                detailed_results=self._compile_detailed_results(
                    file_paths, all_entries, patterns, unique_patterns, issue_results
                ),
            )

            self.last_analysis_result = result
            return result

        except Exception as e:
            return AnalysisResult(
                success=False,
                error_message=f"Analysis failed: {str(e)}",
                execution_time_seconds=time.time() - start_time,
                detailed_results={"exception_type": type(e).__name__},
            )

    def analyze_single_file(self, file_path: str, create_issues: bool = True) -> AnalysisResult:
        """Analyze a single claude-trace file.

        Args:
            file_path: Path to claude-trace JSONL file
            create_issues: Whether to create GitHub issues

        Returns:
            AnalysisResult for the single file
        """
        return self.analyze_trace_files([file_path], create_issues)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of the last analysis performed.

        Returns:
            Dictionary with analysis summary or None if no analysis performed
        """
        if not self.last_analysis_result:
            return {"message": "No analysis has been performed yet"}

        return {
            "last_analysis": self.last_analysis_result.to_dict(),
            "component_statistics": {
                "deduplication": self.deduplication_engine.get_deduplication_report(),
                "issue_generation": self.issue_generator.get_generation_statistics(),
            },
            "github_integration_enabled": self.github_integration_enabled,
        }

    def reset_state(self):
        """Reset internal state for fresh analysis."""
        self.deduplication_engine.reset_cache()
        self.last_analysis_result = None

    def _parse_files(self, file_paths: List[str]) -> List[ParsedEntry]:
        """Parse all JSONL files with error handling.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of all parsed entries from all files

        Raises:
            ValidationError: If critical parsing errors occur
        """
        all_entries = []
        parse_errors = []

        for file_path in file_paths:
            try:
                # Verify file exists
                if not Path(file_path).exists():
                    parse_errors.append(f"File not found: {file_path}")
                    continue

                # Parse file
                entries = self.parser.parse_file(file_path)
                all_entries.extend(entries)

            except ValidationError as e:
                parse_errors.append(f"Validation error in {file_path}: {str(e)}")
            except Exception as e:
                parse_errors.append(f"Unexpected error parsing {file_path}: {str(e)}")

        # If we have some entries, continue despite errors
        if all_entries and parse_errors:
            # Log parse errors but continue
            pass
        elif parse_errors and not all_entries:
            # Critical failure - no entries parsed
            raise ValidationError(f"Failed to parse any files: {'; '.join(parse_errors)}")

        return all_entries

    def _extract_patterns(self, entries: List[ParsedEntry]) -> List[ImprovementPattern]:
        """Extract improvement patterns from parsed entries.

        Args:
            entries: List of parsed entries

        Returns:
            List of identified improvement patterns
        """
        return self.pattern_extractor.extract_patterns(entries)

    def _deduplicate_patterns(self, patterns: List[ImprovementPattern]) -> List[ImprovementPattern]:
        """Deduplicate patterns using multi-layer checking.

        Args:
            patterns: List of patterns to deduplicate

        Returns:
            List of unique patterns
        """
        unique_patterns = []

        for pattern in patterns:
            result = self.deduplication_engine.is_duplicate(pattern)
            if not result.is_duplicate:
                unique_patterns.append(pattern)

        return unique_patterns

    def _create_issues(
        self, patterns: List[ImprovementPattern]
    ) -> "tuple[int, List[IssueCreationResult]]":
        """Create GitHub issues for unique patterns.

        Args:
            patterns: List of unique patterns

        Returns:
            Tuple of (issues_created_count, list_of_results)
        """
        issue_results = []
        successful_creations = 0

        for pattern in patterns:
            result = self.issue_generator.create_issue(pattern)
            issue_results.append(result)

            if result.success:
                successful_creations += 1

        return successful_creations, issue_results

    def _compile_detailed_results(
        self,
        file_paths: List[str],
        entries: List[ParsedEntry],
        patterns: List[ImprovementPattern],
        unique_patterns: List[ImprovementPattern],
        issue_results: List[IssueCreationResult],
    ) -> Dict[str, Any]:
        """Compile detailed results for comprehensive reporting.

        Args:
            file_paths: List of processed file paths
            entries: All parsed entries
            patterns: All identified patterns
            unique_patterns: Unique patterns after deduplication
            issue_results: Results from issue creation

        Returns:
            Dictionary with detailed results
        """
        # Pattern analysis
        pattern_types = {}
        for pattern in patterns:
            pattern_types[pattern.type] = pattern_types.get(pattern.type, 0) + 1

        unique_pattern_types = {}
        for pattern in unique_patterns:
            unique_pattern_types[pattern.type] = unique_pattern_types.get(pattern.type, 0) + 1

        # Issue creation analysis
        successful_issues = [r for r in issue_results if r.success]
        failed_issues = [r for r in issue_results if not r.success]

        # File analysis
        files_by_size = []
        for file_path in file_paths:
            try:
                size = Path(file_path).stat().st_size
                files_by_size.append({"path": file_path, "size_bytes": size})
            except (OSError, FileNotFoundError):
                files_by_size.append({"path": file_path, "size_bytes": 0})

        return {
            "files": {"processed": files_by_size, "total_count": len(file_paths)},
            "entries": {
                "total_parsed": len(entries),
                "by_type": self._count_by_type(entries, "entry_type"),
            },
            "patterns": {
                "total_identified": len(patterns),
                "by_type": pattern_types,
                "unique_count": len(unique_patterns),
                "unique_by_type": unique_pattern_types,
                "deduplication_rate": (
                    (len(patterns) - len(unique_patterns)) / max(len(patterns), 1)
                ),
            },
            "issues": {
                "creation_attempted": len(issue_results),
                "successful": len(successful_issues),
                "failed": len(failed_issues),
                "success_rate": len(successful_issues) / max(len(issue_results), 1),
                "github_integration_enabled": self.github_integration_enabled,
            },
            "component_reports": {
                "deduplication": self.deduplication_engine.get_deduplication_report(),
                "issue_generation": self.issue_generator.get_generation_statistics(),
            },
        }

    def _count_by_type(self, items: List, type_field: str) -> Dict[str, int]:
        """Count items by a specific type field.

        Args:
            items: List of items to count
            type_field: Field name to count by

        Returns:
            Dictionary with counts by type
        """
        counts = {}
        for item in items:
            item_type = getattr(item, type_field, "unknown")
            counts[item_type] = counts.get(item_type, 0) + 1
        return counts
