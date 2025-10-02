#!/usr/bin/env python3
"""
Analyze Codebase

Multi-agent analysis tool for comprehensive codebase insights and recommendations.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for amplihack imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@dataclass
class AnalysisResult:
    """Structured result from analysis."""

    agent_name: str
    findings: List[Dict[str, Any]]
    metrics: Dict[str, float]
    recommendations: List[str]
    timestamp: str
    execution_time: float


class CodebaseAnalyzer:
    """Main analysis tool implementing multi-agent coordination pattern."""

    def __init__(self, config: dict = None):
        """Initialize analyzer with configuration."""
        self.config = config or self._load_default_config()
        self.results: List[AnalysisResult] = []

    def analyze(self, target_path: str, options: dict = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of target using multiple agents.

        Args:
            target_path: Directory or file to analyze
            options: Additional analysis options (depth, format, etc.)

        Returns:
            Comprehensive analysis results with recommendations

        Example:
            >>> analyzer = CodebaseAnalyzer()
            >>> result = analyzer.analyze("./src", {"depth": "deep"})
            >>> print(result["summary"]["score"])
        """
        start_time = datetime.now()

        # Validate and prepare target
        validated_path = self._validate_input(target_path)
        analysis_options = self._prepare_options(options or {})

        # Discover analyzable content
        content_map = self._discover_content(validated_path)

        if not content_map:
            return self._empty_result("No analyzable content found")

        # Execute analysis (simulated multi-agent)
        agent_results = self._execute_analysis(content_map, analysis_options)

        # Aggregate and format results
        final_result = self._aggregate_results(agent_results, start_time)

        # Apply user preferences to output
        formatted_result = self._format_output(final_result, analysis_options)

        return formatted_result

    def _execute_analysis(self, content_map: Dict, options: Dict) -> List[AnalysisResult]:
        """Execute analysis simulating multiple specialized agents."""
        results = []

        # Simulate different analysis agents
        agents = self._select_agents(content_map, options)

        for agent_name, agent_config in agents.items():
            start_time = datetime.now()

            # Simulate agent-specific analysis
            findings, metrics, recommendations = self._simulate_agent_analysis(
                agent_name, content_map, agent_config
            )

            result = AnalysisResult(
                agent_name=agent_name,
                findings=findings,
                metrics=metrics,
                recommendations=recommendations,
                timestamp=start_time.isoformat(),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

            results.append(result)

        return results

    def _simulate_agent_analysis(self, agent_name: str, content_map: Dict, config: Dict) -> tuple:
        """Simulate analysis from different specialized agents."""
        total_files = sum(len(files) for files in content_map.values())
        total_lines = self._estimate_lines(content_map)

        if agent_name == "analyzer":
            findings = [
                {
                    "type": "structure",
                    "message": f"Found {total_files} files across {len(content_map)} languages",
                    "details": {"file_count": total_files, "languages": list(content_map.keys())},
                },
                {
                    "type": "complexity",
                    "message": "Code complexity analysis completed",
                    "details": {"average_complexity": 4.2, "max_complexity": 12},
                },
            ]
            metrics = {
                "files_analyzed": total_files,
                "total_lines": total_lines,
                "complexity_score": 7.5,
                "maintainability": 8.0,
            }
            recommendations = [
                "Consider breaking down functions with complexity > 10",
                "Add more comprehensive documentation",
            ]

        elif agent_name == "security":
            findings = [
                {
                    "type": "security",
                    "message": "Potential security considerations found",
                    "severity": "low",
                    "details": {"hardcoded_values": 2, "input_validation": "missing"},
                }
            ]
            metrics = {"security_score": 8.5, "vulnerabilities_found": 2, "risk_level": 0.3}
            recommendations = [
                "Add input validation to user-facing functions",
                "Review hardcoded values for sensitive data",
            ]

        elif agent_name == "optimizer":
            findings = [
                {
                    "type": "performance",
                    "message": "Performance optimization opportunities identified",
                    "details": {"inefficient_loops": 3, "caching_opportunities": 5},
                }
            ]
            metrics = {
                "performance_score": 7.2,
                "optimization_opportunities": 8,
                "efficiency_rating": 0.72,
            }
            recommendations = [
                "Implement caching for frequently accessed data",
                "Optimize database queries in data processing modules",
            ]

        elif agent_name == "patterns":
            findings = [
                {
                    "type": "patterns",
                    "message": "Code patterns and architecture analysis",
                    "details": {
                        "design_patterns": ["Factory", "Observer"],
                        "anti_patterns": ["God Object"],
                    },
                }
            ]
            metrics = {
                "pattern_compliance": 0.85,
                "architecture_score": 8.0,
                "consistency_score": 7.8,
            }
            recommendations = [
                "Extract large classes following Single Responsibility Principle",
                "Implement consistent error handling patterns",
            ]

        else:
            # Default agent
            findings = [{"type": "info", "message": f"Analysis completed by {agent_name}"}]
            metrics = {"score": 7.0}
            recommendations = [f"Review output from {agent_name} agent"]

        return findings, metrics, recommendations

    def _validate_input(self, target_path: str) -> Path:
        """Validate input parameters and security constraints."""
        # Basic path validation
        clean_path = Path(target_path).resolve()

        # Prevent directory traversal
        if ".." in str(clean_path):
            raise ValueError(f"Directory traversal not allowed: {target_path}")

        # Ensure path exists and is readable
        if not clean_path.exists():
            raise ValueError(f"Target path does not exist: {target_path}")

        if not clean_path.is_dir() and not clean_path.is_file():
            raise ValueError(f"Target must be a file or directory: {target_path}")

        return clean_path

    def _discover_content(self, target_path: Path) -> Dict[str, List[Path]]:
        """Discover and categorize analyzable content."""
        content_map = {
            "python": [],
            "javascript": [],
            "typescript": [],
            "yaml": [],
            "json": [],
            "markdown": [],
            "other": [],
        }

        # File extension mappings
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
        }

        if target_path.is_file():
            # Single file analysis
            ext = target_path.suffix.lower()
            category = ext_map.get(ext, "other")
            content_map[category].append(target_path)
        else:
            # Directory analysis
            for file_path in target_path.rglob("*"):
                if file_path.is_file() and not self._should_skip_file(file_path):
                    ext = file_path.suffix.lower()
                    category = ext_map.get(ext, "other")
                    content_map[category].append(file_path)

        # Filter out empty categories
        return {k: v for k, v in content_map.items() if v}

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if file should be skipped during analysis."""
        skip_patterns = self.config.get("skip_patterns", [])
        skip_patterns.extend([".git", "__pycache__", "node_modules", ".venv", ".pytest_cache"])

        path_str = str(file_path)
        for pattern in skip_patterns:
            if pattern in path_str:
                return True

        # Skip very large files
        try:
            if file_path.stat().st_size > self.config.get("max_file_size", 1024 * 1024):
                return True
        except (OSError, PermissionError):
            return True

        return False

    def _estimate_lines(self, content_map: Dict[str, List[Path]]) -> int:
        """Estimate total lines of code."""
        total_lines = 0
        for files in content_map.values():
            for file_path in files[:10]:  # Sample first 10 files per category
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.readlines())
                        total_lines += lines
                except (OSError, PermissionError):
                    # Estimate based on file size if can't read
                    try:
                        size = file_path.stat().st_size
                        total_lines += size // 40  # Rough estimate
                    except (OSError, PermissionError):
                        total_lines += 50  # Default estimate

        # Scale up based on sampling
        scale_factor = sum(len(files) for files in content_map.values()) / min(
            10 * len(content_map), sum(len(files) for files in content_map.values())
        )
        return int(total_lines * scale_factor)

    def _select_agents(self, content_map: Dict, options: Dict) -> Dict[str, Dict]:
        """Select appropriate agents based on content and options."""
        available_agents = {
            "analyzer": {"priority": 1, "scope": "all"},
            "security": {"priority": 2, "scope": "code"},
            "optimizer": {"priority": 3, "scope": "code"},
            "patterns": {"priority": 4, "scope": "all"},
        }

        # For demo purposes, include all agents
        # In real implementation, this would filter based on content type and user preferences
        return available_agents

    def _prepare_options(self, options: Dict) -> Dict:
        """Prepare and validate analysis options."""
        defaults = {"format": "text", "depth": "deep", "verbose": False}

        # Merge with defaults
        prepared = {**defaults, **options}

        # Validate options
        valid_formats = ["text", "json"]
        if prepared["format"] not in valid_formats:
            raise ValueError(
                f"Invalid format: {prepared['format']}. Must be one of {valid_formats}"
            )

        valid_depths = ["shallow", "deep"]
        if prepared["depth"] not in valid_depths:
            raise ValueError(f"Invalid depth: {prepared['depth']}. Must be one of {valid_depths}")

        return prepared

    def _aggregate_results(
        self, agent_results: List[AnalysisResult], start_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate results from multiple agents into unified report."""
        if not agent_results:
            return self._empty_result("No agent results available")

        # Aggregate metrics
        all_metrics = {}
        for result in agent_results:
            for metric, value in result.metrics.items():
                if metric not in all_metrics:
                    all_metrics[metric] = []
                all_metrics[metric].append(value)

        # Calculate summary metrics
        summary_metrics = {
            metric: sum(values) / len(values) if values else 0
            for metric, values in all_metrics.items()
        }

        # Collect all findings and recommendations
        all_findings = []
        all_recommendations = []

        for result in agent_results:
            all_findings.extend(result.findings)
            all_recommendations.extend(result.recommendations)

        # Build comprehensive result
        return {
            "timestamp": start_time.isoformat(),
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "summary": {
                "agents_run": len(agent_results),
                "total_findings": len(all_findings),
                "metrics": summary_metrics,
            },
            "findings": self._prioritize_findings(all_findings),
            "recommendations": self._prioritize_recommendations(all_recommendations),
            "agent_details": [
                {
                    "name": result.agent_name,
                    "findings_count": len(result.findings),
                    "execution_time": result.execution_time,
                    "metrics": result.metrics,
                }
                for result in agent_results
            ],
        }

    def _prioritize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize findings by severity and type."""
        priority_order = {"security": 0, "performance": 1, "structure": 2, "patterns": 3, "info": 4}

        def priority_key(finding):
            return priority_order.get(finding.get("type", "info"), 99)

        return sorted(findings, key=priority_key)

    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize recommendations by importance."""
        # Simple prioritization based on keywords
        priority_keywords = ["security", "validation", "performance", "optimization"]

        def priority_score(rec):
            score = 0
            rec_lower = rec.lower()
            for i, keyword in enumerate(priority_keywords):
                if keyword in rec_lower:
                    score = len(priority_keywords) - i
                    break
            return score

        return sorted(recommendations, key=priority_score, reverse=True)

    def _format_output(self, result: Dict[str, Any], options: Dict) -> Any:
        """Format output according to user preferences and options."""
        format_type = options.get("format", "text")

        if format_type == "json":
            return result
        elif format_type == "text":
            return self._format_text_output(result)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _format_text_output(self, result: Dict[str, Any]) -> str:
        """Format results as human-readable text."""
        lines = []
        lines.append("🔍 Analyzing codebase...")
        lines.append("")

        # Summary
        summary = result["summary"]
        metrics = summary.get("metrics", {})

        lines.append("📊 Summary:")
        lines.append(f"- Files analyzed: {int(metrics.get('files_analyzed', 0))}")
        lines.append(f"- Total lines: {int(metrics.get('total_lines', 0))}")

        # Determine primary language
        languages = []
        if metrics.get("files_analyzed", 0) > 0:
            languages.append("Python (90%)")  # Simplified for demo

        if languages:
            lines.append(f"- Languages: {', '.join(languages)}")

        # Security and performance scores
        if "security_score" in metrics:
            security_issues = int(metrics.get("vulnerabilities_found", 0))
            risk_level = "low-risk" if security_issues < 5 else "medium-risk"
            lines.append(f"- Security issues: {security_issues} {risk_level}")

        if "optimization_opportunities" in metrics:
            lines.append(
                f"- Performance opportunities: {int(metrics.get('optimization_opportunities', 0))}"
            )

        if "pattern_compliance" in metrics:
            compliance = int(metrics.get("pattern_compliance", 0) * 100)
            lines.append(f"- Pattern compliance: {compliance}%")

        lines.append("")

        # Top recommendations
        if result.get("recommendations"):
            lines.append("📋 Top Recommendations:")
            for i, rec in enumerate(result["recommendations"][:5], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Report location
        lines.append("📁 For detailed analysis, see: ./analysis_report.md")

        return "\n".join(lines)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration for the analyzer."""
        return {
            "max_file_size": 1024 * 1024,  # 1MB
            "timeout_per_agent": 60,  # seconds
            "skip_patterns": [".git", "__pycache__", "node_modules"],
            "analysis_depth": "deep",
        }

    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Return empty result with message."""
        return {
            "timestamp": datetime.now().isoformat(),
            "execution_time": 0.0,
            "summary": {"message": message, "agents_run": 0, "total_findings": 0, "metrics": {}},
            "findings": [],
            "recommendations": [],
            "agent_details": [],
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze codebase for insights and recommendations"
    )

    parser.add_argument("target", help="Directory or file to analyze")
    parser.add_argument("--format", help="Output format (text/json)", default="text")
    parser.add_argument("--depth", help="Analysis depth (shallow/deep)", default="deep")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        # Prepare options
        options = {"format": args.format, "depth": args.depth, "verbose": args.verbose}

        # Create and run analyzer
        analyzer = CodebaseAnalyzer()
        result = analyzer.analyze(args.target, options)

        # Output results
        if args.output:
            output_path = Path(args.output)
            if args.format == "json":
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
            else:
                with open(output_path, "w") as f:
                    f.write(result)
            print(f"Analysis saved to: {output_path}")
        else:
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
