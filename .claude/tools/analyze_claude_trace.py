#!/usr/bin/env python3
"""
Comprehensive Claude-Trace Log Analyzer
Analyzes claude-trace logs to identify patterns, errors, and improvement opportunities
"""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


class ClaudeTraceAnalyzer:
    def __init__(self, log_dir: str = "~/src/.claude-trace"):
        self.log_dir = Path(os.path.expanduser(log_dir))
        self.results = {
            "tool_usage": Counter(),
            "command_patterns": Counter(),
            "file_operations": Counter(),
            "error_patterns": Counter(),
            "performance_issues": [],
            "repetitive_patterns": defaultdict(list),
            "api_calls": Counter(),
            "workflow_patterns": [],
            "improvement_opportunities": [],
        }

    def analyze_all_logs(self, recent_n: int = 10) -> Dict[str, Any]:
        """Analyze the most recent N log files"""
        log_files = sorted(
            [f for f in self.log_dir.glob("*.jsonl")], key=lambda x: x.stat().st_mtime, reverse=True
        )[:recent_n]

        print(f"Analyzing {len(log_files)} log files...")

        for log_file in log_files:
            self._analyze_log_file(log_file)

        return self._generate_report()

    def _analyze_log_file(self, log_file: Path) -> None:
        """Analyze a single log file"""
        print(f"Processing {log_file.name}...")

        with open(log_file, "r") as f:
            session_data = {
                "requests": [],
                "responses": [],
                "tool_sequence": [],
                "timings": [],
                "errors": [],
            }

            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())

                    # Analyze request patterns
                    if "request" in entry:
                        self._analyze_request(entry["request"], session_data)

                    # Analyze response patterns
                    if "response" in entry:
                        self._analyze_response(entry["response"], session_data)

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error at line {line_num}: {e}")

            # Analyze session patterns
            self._analyze_session_patterns(session_data, log_file.name)

    def _analyze_request(self, request: Dict, session_data: Dict) -> None:
        """Analyze request patterns"""
        if "body" in request:
            body = request["body"]

            # Track API model usage
            if "model" in body:
                self.results["api_calls"][body["model"]] += 1

            # Analyze messages for tool usage
            if "messages" in body:
                for message in body["messages"]:
                    if isinstance(message, dict):
                        # Look for tool use patterns
                        if "content" in message:
                            content = str(message["content"])
                            self._extract_patterns(content)

            # Track timing
            if "timestamp" in request:
                session_data["timings"].append(request["timestamp"])

    def _analyze_response(self, response: Dict, session_data: Dict) -> None:
        """Analyze response patterns"""
        # Check for errors
        if response.get("status_code", 200) >= 400:
            error_info = {
                "status": response.get("status_code"),
                "headers": response.get("headers", {}),
                "body": response.get("body", ""),
            }
            session_data["errors"].append(error_info)
            self.results["error_patterns"][f"HTTP_{error_info['status']}"] += 1

        # Analyze response body for patterns
        if "body" in response:
            self._analyze_response_body(response["body"])

    def _analyze_response_body(self, body: Any) -> None:
        """Analyze response body for patterns"""
        if isinstance(body, dict):
            # Check for tool usage in responses
            if "type" in body:
                if body["type"] == "tool_use":
                    tool_name = body.get("name", "unknown")
                    self.results["tool_usage"][tool_name] += 1

                    # Analyze tool inputs
                    if "input" in body and tool_name == "Bash":
                        command = body["input"].get("command", "")
                        if command:
                            base_cmd = command.split()[0] if command.split() else ""
                            self.results["command_patterns"][base_cmd] += 1

                    elif "input" in body and tool_name in ["Read", "Write", "Edit", "MultiEdit"]:
                        self.results["file_operations"][tool_name] += 1

            # Check for usage metrics
            if "usage" in body:
                usage = body["usage"]
                if "input_tokens" in usage and "output_tokens" in usage:
                    total = usage["input_tokens"] + usage["output_tokens"]
                    if total > 100000:  # Flag large token usage
                        self.results["performance_issues"].append(
                            {"type": "high_token_usage", "tokens": total}
                        )

    def _extract_patterns(self, content: str) -> None:
        """Extract patterns from content"""
        # Look for repetitive file operations
        file_pattern = r'(Read|Write|Edit|MultiEdit).*?file_path.*?(["\'])(.+?)\2'
        for match in re.finditer(file_pattern, content, re.IGNORECASE):
            operation, _, filepath = match.groups()
            key = f"{operation}:{filepath}"
            self.results["repetitive_patterns"][key].append(1)

        # Look for repetitive commands
        bash_pattern = r'Bash.*?command.*?(["\'])(.+?)\1'
        for match in re.finditer(bash_pattern, content, re.IGNORECASE):
            _, command = match.groups()
            if command:
                self.results["repetitive_patterns"][f"cmd:{command}"].append(1)

    def _analyze_session_patterns(self, session_data: Dict, log_name: str) -> None:
        """Analyze patterns within a session"""
        # Check for performance issues
        if session_data["timings"]:
            timings = sorted(session_data["timings"])
            if len(timings) > 1:
                duration = timings[-1] - timings[0]
                if duration > 3600:  # Session longer than 1 hour
                    self.results["performance_issues"].append(
                        {"type": "long_session", "duration_seconds": duration, "log": log_name}
                    )

        # Track error rates
        if session_data["errors"]:
            error_rate = len(session_data["errors"]) / max(len(session_data["requests"]), 1)
            if error_rate > 0.1:  # More than 10% errors
                self.results["performance_issues"].append(
                    {"type": "high_error_rate", "rate": error_rate, "log": log_name}
                )

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        # Identify improvement opportunities
        self._identify_improvements()

        return {
            "summary": {
                "total_tool_calls": sum(self.results["tool_usage"].values()),
                "total_commands": sum(self.results["command_patterns"].values()),
                "total_file_ops": sum(self.results["file_operations"].values()),
                "total_errors": sum(self.results["error_patterns"].values()),
                "performance_issues": len(self.results["performance_issues"]),
            },
            "top_tools": self.results["tool_usage"].most_common(10),
            "top_commands": self.results["command_patterns"].most_common(10),
            "file_operations": dict(self.results["file_operations"]),
            "error_patterns": dict(self.results["error_patterns"]),
            "performance_issues": self.results["performance_issues"][:10],
            "repetitive_actions": self._find_repetitive_actions(),
            "improvement_opportunities": self.results["improvement_opportunities"],
            "api_usage": dict(self.results["api_calls"]),
        }

    def _find_repetitive_actions(self) -> List[Dict]:
        """Find actions that are repeated frequently"""
        repetitive = []
        for action, occurrences in self.results["repetitive_patterns"].items():
            if len(occurrences) >= 3:  # Repeated 3+ times
                repetitive.append(
                    {
                        "action": action,
                        "count": len(occurrences),
                        "type": "command" if action.startswith("cmd:") else "file_operation",
                    }
                )
        return sorted(repetitive, key=lambda x: x["count"], reverse=True)[:20]

    def _identify_improvements(self) -> None:
        """Identify specific improvement opportunities"""
        improvements = []

        # Check for repetitive file reads
        file_reads = [k for k in self.results["repetitive_patterns"] if k.startswith("Read:")]
        if len(file_reads) > 5:
            improvements.append(
                {
                    "category": "automation",
                    "issue": "Repetitive file reads detected",
                    "suggestion": "Implement file caching or batch reading",
                    "impact": "high",
                }
            )

        # Check for repetitive commands
        repetitive_cmds = [
            k
            for k, v in self.results["repetitive_patterns"].items()
            if k.startswith("cmd:") and len(v) >= 5
        ]
        if repetitive_cmds:
            improvements.append(
                {
                    "category": "automation",
                    "issue": f"Found {len(repetitive_cmds)} repetitive commands",
                    "suggestion": "Create custom tools or aliases for common operations",
                    "impact": "medium",
                }
            )

        # Check for performance issues
        if self.results["performance_issues"]:
            long_sessions = [
                p for p in self.results["performance_issues"] if p["type"] == "long_session"
            ]
            if long_sessions:
                improvements.append(
                    {
                        "category": "performance",
                        "issue": f"{len(long_sessions)} long sessions detected",
                        "suggestion": "Implement session checkpointing and resumption",
                        "impact": "high",
                    }
                )

        # Check for high token usage
        high_token = [
            p for p in self.results["performance_issues"] if p["type"] == "high_token_usage"
        ]
        if high_token:
            improvements.append(
                {
                    "category": "optimization",
                    "issue": f"{len(high_token)} instances of high token usage",
                    "suggestion": "Implement context pruning and summarization",
                    "impact": "medium",
                }
            )

        # Check error patterns
        if self.results["error_patterns"]:
            total_errors = sum(self.results["error_patterns"].values())
            if total_errors > 10:
                improvements.append(
                    {
                        "category": "reliability",
                        "issue": f"{total_errors} errors detected",
                        "suggestion": "Implement better error handling and retry logic",
                        "impact": "high",
                    }
                )

        self.results["improvement_opportunities"] = improvements


def main():
    analyzer = ClaudeTraceAnalyzer()
    report = analyzer.analyze_all_logs(recent_n=10)

    # Print report
    print("\n" + "=" * 60)
    print("CLAUDE-TRACE LOG ANALYSIS REPORT")
    print("=" * 60)

    print("\n## SUMMARY")
    for key, value in report["summary"].items():
        print(f"  {key}: {value}")

    print("\n## TOP TOOLS USED")
    for tool, count in report["top_tools"]:
        print(f"  {tool}: {count}")

    print("\n## TOP COMMANDS")
    for cmd, count in report["top_commands"]:
        print(f"  {cmd}: {count}")

    print("\n## FILE OPERATIONS")
    for op, count in report["file_operations"].items():
        print(f"  {op}: {count}")

    print("\n## ERROR PATTERNS")
    for error, count in report["error_patterns"].items():
        print(f"  {error}: {count}")

    print("\n## REPETITIVE ACTIONS")
    for action in report["repetitive_actions"][:10]:
        print(f"  {action['type']}: {action['action']} ({action['count']} times)")

    print("\n## IMPROVEMENT OPPORTUNITIES")
    for improvement in report["improvement_opportunities"]:
        print(f"\n  [{improvement['category'].upper()}] {improvement['issue']}")
        print(f"    Suggestion: {improvement['suggestion']}")
        print(f"    Impact: {improvement['impact']}")

    print("\n## API USAGE")
    for model, count in report["api_usage"].items():
        print(f"  {model}: {count} calls")

    # Save detailed report
    output_file = Path("claude_trace_analysis_results.json")
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nDetailed report saved to: {output_file}")


if __name__ == "__main__":
    main()
