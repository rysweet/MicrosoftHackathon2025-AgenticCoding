#!/usr/bin/env python3
"""
Stage 2 Reflection System - Convert insights to PRs

Reads Stage 1 reflection output and converts high-priority patterns into
actionable pull requests and GitHub issues.

This module implements the second stage of the reflection pipeline:
1. Reads Stage 1 analysis output
2. Groups related improvements
3. Generates PR descriptions from templates
4. Creates GitHub issues and PRs
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import GitHub issue creator - use absolute import since we added to path
sys.path.insert(0, str(project_root / ".claude" / "tools"))
from github_issue import create_issue  # noqa: E402


class PatternToPRConverter:
    """Convert reflection patterns into PR proposals."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analysis_dir = project_root / ".claude" / "runtime" / "analysis"
        self._init_templates()

    def _init_templates(self):
        """Initialize PR templates for common patterns."""
        self.templates = {
            "repeated_commands": {
                "title": "Automate repetitive {command_type} operations",
                "body": """## Problem
The session analysis identified {count} repetitive {command_type} operations that could be
automated.

## Pattern Details
{pattern_details}

## Proposed Solution
Create an automation script that:
- Consolidates common {command_type} operations
- Provides a single command interface
- Includes error handling and retry logic
- Supports batch processing where applicable

## Implementation
- [ ] Create automation script in `.claude/tools/automation/`
- [ ] Add command-line interface
- [ ] Include comprehensive error handling
- [ ] Add documentation and usage examples
- [ ] Write unit tests

## Benefits
- Reduces manual repetition
- Improves consistency
- Saves developer time
- Reduces error potential

Generated from session reflection analysis.""",
                "labels": ["automation", "enhancement", "developer-experience"],
            },
            "error_patterns": {
                "title": "Improve error handling for {error_type}",
                "body": """## Problem
Analysis detected {count} instances of {error_type} errors that lack proper handling.

## Error Details
{error_details}

## Proposed Solution
Implement comprehensive error handling:
- Add specific error recovery strategies
- Improve error messages with actionable guidance
- Add retry logic where appropriate
- Log errors for debugging

## Implementation
- [ ] Identify all error points in affected modules
- [ ] Implement try-catch blocks with specific handlers
- [ ] Add error recovery mechanisms
- [ ] Improve error messaging
- [ ] Add error tracking/metrics

## Expected Outcome
- Reduced error occurrence
- Better error recovery
- Clearer error messages
- Improved debugging capability

Generated from session reflection analysis.""",
                "labels": ["bug", "error-handling", "reliability"],
            },
            "user_frustration": {
                "title": "Architecture review: Address {pain_point}",
                "body": """## Background
Session analysis indicates user frustration with {pain_point}.

## Symptoms
{symptom_details}

## Root Cause Analysis Required
This issue requires architectural review to identify:
- Design limitations causing the frustration
- Alternative approaches
- Potential refactoring opportunities

## Proposed Investigation
- [ ] Analyze current architecture for {pain_point}
- [ ] Document pain points and limitations
- [ ] Research alternative patterns
- [ ] Create proof of concept for improvements
- [ ] Estimate refactoring effort

## Success Criteria
- Clear understanding of root causes
- Documented improvement proposals
- Actionable refactoring plan

Generated from session reflection analysis.""",
                "labels": ["architecture", "investigation", "user-experience"],
            },
            "long_session": {
                "title": "Task decomposition guide for {task_type}",
                "body": """## Problem
Analysis shows extended session duration for {task_type} tasks, indicating need for better
decomposition.

## Session Metrics
{session_metrics}

## Proposed Solution
Create a task decomposition guide that:
- Breaks down complex {task_type} tasks into manageable chunks
- Provides clear checkpoints and validation steps
- Includes time estimates for subtasks
- Offers parallel execution opportunities

## Deliverables
- [ ] Task decomposition template
- [ ] Step-by-step guide for {task_type}
- [ ] Checkpoint validation criteria
- [ ] Time estimation guidelines
- [ ] Parallelization opportunities

## Benefits
- Reduced cognitive load
- Better progress tracking
- Improved time estimation
- Faster task completion

Generated from session reflection analysis.""",
                "labels": ["documentation", "process", "efficiency"],
            },
            "performance_bottleneck": {
                "title": "Optimize performance bottleneck in {component}",
                "body": """## Problem
Performance analysis identified bottlenecks in {component}.

## Bottleneck Details
{bottleneck_details}

## Proposed Optimizations
- Implement caching strategies
- Optimize data structures
- Add parallel processing
- Reduce redundant operations

## Implementation Plan
- [ ] Profile current performance
- [ ] Implement optimizations
- [ ] Measure improvement
- [ ] Add performance tests
- [ ] Document optimization techniques

## Expected Impact
- {expected_improvement}% performance improvement
- Better resource utilization
- Improved user experience

Generated from session reflection analysis.""",
                "labels": ["performance", "optimization"],
            },
            "missing_tooling": {
                "title": "Add tooling for {capability}",
                "body": """## Gap Identified
Session analysis reveals missing tooling for {capability}.

## Current Limitations
{limitation_details}

## Proposed Tool
Build a tool that:
{tool_features}

## Implementation
- [ ] Design tool interface
- [ ] Implement core functionality
- [ ] Add CLI/API access
- [ ] Write documentation
- [ ] Create usage examples

## Expected Benefits
- Streamlined {capability} workflow
- Reduced manual effort
- Improved consistency

Generated from session reflection analysis.""",
                "labels": ["tooling", "enhancement", "developer-experience"],
            },
            "session_summary": {
                "title": "Session Analysis Summary",
                "body": """## Session Metrics

{summary_details}

## Analysis Overview
This session was analyzed for improvement opportunities.

### Key Statistics
- **Messages**: {total_messages}
- **Tool Uses**: {tool_uses}
- **Duration**: {duration} minutes
- **Errors**: {errors}

## Reflection Status
✅ Session analyzed by Stage 2 reflection system
📊 Pattern detection completed
📝 Report generated

This summary confirms that the session was successfully processed through the two-stage reflection system, providing comprehensive analysis even when no specific improvement patterns were detected.

Generated from session reflection analysis.""",
                "labels": ["reflection", "session-summary", "analysis"],
            },
        }

    def analyze_stage1_output(self, stage1_file: Path) -> Dict[str, Any]:
        """Read and analyze Stage 1 reflection output."""
        with open(stage1_file, "r") as f:
            data = json.load(f)

        # Extract patterns and priorities
        patterns = []

        # Check for repeated commands
        if "tool_usage" in data.get("metrics", {}):
            tool_stats = data["metrics"]["tool_usage"]
            for tool, count in tool_stats.items():
                if count > 3:  # Lowered threshold for repetition detection
                    patterns.append(
                        {
                            "type": "repeated_commands",
                            "priority": "high" if count > 10 else "medium",
                            "data": {
                                "command_type": tool,
                                "count": count,
                                "pattern_details": f"Tool '{tool}' was used {count} times",
                            },
                        }
                    )

        # Check for error patterns
        if "errors" in data.get("metrics", {}):
            error_count = data["metrics"]["errors"]
            if error_count > 1:  # Lowered threshold for error detection
                patterns.append(
                    {
                        "type": "error_patterns",
                        "priority": "high",
                        "data": {
                            "error_type": "general",
                            "count": error_count,
                            "error_details": f"Session had {error_count} errors",
                        },
                    }
                )

        # Check for long sessions
        if "duration_minutes" in data.get("metrics", {}):
            duration = data["metrics"]["duration_minutes"]
            if duration > 15:  # Lowered threshold for long session detection
                patterns.append(
                    {
                        "type": "long_session",
                        "priority": "medium",
                        "data": {
                            "task_type": "general",
                            "session_metrics": f"Session duration: {duration} minutes",
                        },
                    }
                )

        # Extract user frustration indicators
        if "learnings" in data:
            frustration_keywords = ["difficult", "stuck", "confused", "unclear", "complex"]
            for learning in data["learnings"]:
                if any(kw in learning.get("preview", "").lower() for kw in frustration_keywords):
                    patterns.append(
                        {
                            "type": "user_frustration",
                            "priority": "high",
                            "data": {
                                "pain_point": "workflow complexity",
                                "symptom_details": learning.get("preview", "")[:200],
                            },
                        }
                    )
                    break

        # Always add a session summary pattern for complete analysis
        session_metrics = data.get("metrics", {})
        patterns.append(
            {
                "type": "session_summary",
                "priority": "low",
                "data": {
                    "summary_type": "general",
                    "total_messages": session_metrics.get("message_count", 0),
                    "tool_uses": session_metrics.get("tool_uses", 0),
                    "duration": session_metrics.get("duration_minutes", 0),
                    "errors": session_metrics.get("errors", 0),
                    "summary_details": f"Session completed with {session_metrics.get('message_count', 0)} messages, {session_metrics.get('tool_uses', 0)} tool uses, {session_metrics.get('errors', 0)} errors in {session_metrics.get('duration_minutes', 0)} minutes",
                },
            }
        )

        return {
            "patterns": patterns,
            "session_id": data.get("session_id", "unknown"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
        }

    def group_related_improvements(self, patterns: List[Dict]) -> List[Dict]:
        """Group related patterns for consolidated PRs."""
        # Group by pattern type and priority
        grouped = {}

        for pattern in patterns:
            key = (pattern["type"], pattern["priority"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(pattern)

        # Convert to list of PR proposals
        proposals = []
        for (pattern_type, priority), items in grouped.items():
            if len(items) == 1:
                proposals.append(items[0])
            else:
                # Merge similar patterns
                merged_data = {}
                for item in items:
                    for k, v in item["data"].items():
                        if k not in merged_data:
                            merged_data[k] = v
                        elif isinstance(v, int):
                            merged_data[k] = merged_data.get(k, 0) + v
                        elif isinstance(v, str) and v not in str(merged_data.get(k, "")):
                            merged_data[k] = f"{merged_data.get(k, '')}\n- {v}"

                proposals.append(
                    {
                        "type": pattern_type,
                        "priority": priority,
                        "data": merged_data,
                        "merged_count": len(items),
                    }
                )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        proposals.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return proposals

    def generate_pr_content(self, pattern: Dict) -> Tuple[str, str, List[str]]:
        """Generate PR title, body, and labels from pattern."""
        template = self.templates.get(pattern["type"])
        if not template:
            # Fallback for unknown pattern types
            return (
                f"Improvement: Address {pattern['type']}",
                (
                    "Pattern analysis identified improvements needed.\n\n"
                    f"Details: {json.dumps(pattern['data'], indent=2)}"
                ),
                ["enhancement"],
            )

        # Format the template with pattern data
        title = template["title"].format(**pattern["data"])
        body = template["body"].format(**pattern["data"])
        labels = template["labels"].copy()

        # Add priority label
        if pattern["priority"] == "high":
            labels.append("high-priority")

        return title, body, labels

    def create_pr_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create a new branch for the PR with proper validation."""
        # Validate branch name to prevent injection
        if not re.match(r"^[a-zA-Z0-9/_-]+$", branch_name):
            return {"success": False, "error": "Invalid branch name format"}

        try:
            # Check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                capture_output=True,
                cwd=self.project_root,
                timeout=10,
            )

            if result.returncode == 0:
                # Branch exists, switch to it
                checkout_result = subprocess.run(
                    ["git", "checkout", branch_name],
                    capture_output=True,
                    cwd=self.project_root,
                    timeout=10,
                )
                if checkout_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to checkout branch: {checkout_result.stderr.decode()}",
                    }
            else:
                # Create new branch
                create_result = subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    capture_output=True,
                    cwd=self.project_root,
                    timeout=10,
                )
                if create_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Failed to create branch: {create_result.stderr.decode()}",
                    }

            return {"success": True}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Git command failed: {str(e)}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}

    def create_pr(self, title: str, body: str, branch: str, labels: List[str]) -> Dict[str, Any]:
        """Create a pull request using gh CLI with proper validation."""
        # Validate inputs to prevent injection
        if not title or len(title) > 256:
            return {"success": False, "error": "Invalid title length"}

        if not body or len(body) > 65536:  # 64KB limit
            return {"success": False, "error": "Invalid body length"}

        if not re.match(r"^[a-zA-Z0-9/_-]+$", branch):
            return {"success": False, "error": "Invalid branch name format"}

        # Validate labels
        for label in labels:
            if not re.match(r"^[a-zA-Z0-9-_]+$", label):
                return {"success": False, "error": f"Invalid label format: {label}"}

        try:
            # Create PR with validated inputs
            cmd = ["gh", "pr", "create", "--title", title, "--body", body]

            # Add validated labels
            for label in labels[:5]:  # Limit to 5 labels
                cmd.extend(["--label", label])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,  # 30 second timeout
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                # Extract PR number safely
                match = re.search(r"/pull/(\d+)$", pr_url)
                pr_number = int(match.group(1)) if match else None

                return {"success": True, "pr_url": pr_url, "pr_number": pr_number}
            else:
                # Limit error length
                return {"success": False, "error": result.stderr.strip()[:1000]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "PR creation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)[:1000]}  # Limit error length

    def convert_to_prs(self, stage1_file: Path, create_prs: bool = False) -> Dict[str, Any]:
        """Main method to convert Stage 1 output to PRs."""
        # Analyze Stage 1 output
        analysis = self.analyze_stage1_output(stage1_file)

        # Group related improvements
        proposals = self.group_related_improvements(analysis["patterns"])

        # Generate PR content
        results = {"proposals": [], "created_issues": [], "created_prs": [], "errors": []}

        for i, proposal in enumerate(proposals):
            title, body, labels = self.generate_pr_content(proposal)

            pr_info = {
                "title": title,
                "body": body,
                "labels": labels,
                "priority": proposal["priority"],
                "pattern_type": proposal["type"],
            }

            results["proposals"].append(pr_info)

            if create_prs and proposal["priority"] == "high":
                # Only create PRs for high-priority items
                if proposal["type"] in ["error_patterns", "user_frustration"]:
                    # Create as issue for investigation
                    issue_result = create_issue(title=title, body=body, labels=labels)

                    if issue_result["success"]:
                        results["created_issues"].append(
                            {
                                "number": issue_result["issue_number"],
                                "url": issue_result["issue_url"],
                                "title": title,
                            }
                        )
                    else:
                        results["errors"].append(
                            {
                                "type": "issue_creation",
                                "title": title,
                                "error": issue_result.get("error"),
                            }
                        )
                else:
                    # Create as PR with implementation stub
                    branch_name = (
                        f"auto/reflection-{proposal['type']}-"
                        f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    )

                    if self.create_pr_branch(branch_name):
                        # Create implementation stub
                        # Create investigation issue for complex patterns
                        issue_result = self._create_implementation_issue(proposal)
                        if issue_result["success"]:
                            results["created_issues"].append(
                                {
                                    "number": issue_result.get("issue_number"),
                                    "url": issue_result["issue_url"],
                                    "title": issue_result["title"],
                                }
                            )

                        # Commit changes
                        try:
                            subprocess.run(["git", "add", "-A"], check=True, cwd=self.project_root)
                            subprocess.run(
                                [
                                    "git",
                                    "commit",
                                    "-m",
                                    f"Auto: {title}\n\nGenerated from reflection analysis",
                                ],
                                check=True,
                                cwd=self.project_root,
                            )

                            # Create PR
                            pr_result = self.create_pr(title, body, branch_name, labels)

                            if pr_result["success"]:
                                results["created_prs"].append(
                                    {
                                        "number": pr_result.get("pr_number"),
                                        "url": pr_result["pr_url"],
                                        "title": title,
                                        "branch": branch_name,
                                    }
                                )
                            else:
                                results["errors"].append(
                                    {
                                        "type": "pr_creation",
                                        "title": title,
                                        "error": pr_result.get("error"),
                                    }
                                )
                        except subprocess.CalledProcessError as e:
                            results["errors"].append(
                                {"type": "git_operation", "title": title, "error": str(e)}
                            )

        return results

    def _create_implementation_issue(self, proposal: Dict) -> Dict[str, Any]:
        """Create GitHub issue for complex patterns requiring investigation."""
        title, body, labels = self.generate_pr_content(proposal)

        # Convert PR title to issue title
        issue_title = title.replace("feat:", "investigate:").replace("refactor:", "investigate:")

        # Create investigation issue body
        issue_body = f"""## Investigation Required

This issue was automatically created from reflection analysis.

## Pattern Detected
- **Type**: {proposal["type"]}
- **Priority**: {proposal["priority"]}

## Analysis Details
{body}

## Next Steps
1. Review the detected pattern
2. Determine if automation/tooling is beneficial
3. Create implementation plan
4. Implement solution if justified

## Context
This pattern was detected during session reflection and requires human investigation
to determine the best approach."""

        try:
            # Create issue using existing GitHub integration
            issue_result = create_issue(
                title=issue_title,
                body=issue_body,
                labels=["investigation", "reflection-generated"] + labels,
            )

            if issue_result.get("success"):
                return {
                    "success": True,
                    "issue_url": issue_result.get("issue_url"),
                    "issue_number": issue_result.get("issue_number"),
                    "title": issue_title,
                }
            else:
                return {
                    "success": False,
                    "error": issue_result.get("error", "Unknown error creating issue"),
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to create issue: {str(e)}"}


class ReflectionReportGenerator:
    """Generate comprehensive reflection reports."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / ".claude" / "runtime" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        session_summary: Dict[str, Any],
        stage1_analysis: Dict[str, Any],
        stage2_results: Dict[str, Any],
    ) -> str:
        """Generate a comprehensive markdown report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# Reflection Analysis Report
Generated: {timestamp}

## Session Summary
- **Session ID**: {session_summary.get("session_id", "unknown")}
- **Duration**: {session_summary.get("metrics", {}).get("duration_minutes", "N/A")} minutes
- **Messages**: {session_summary.get("metrics", {}).get("message_count", 0)}
- **Tool Uses**: {session_summary.get("metrics", {}).get("tool_uses", 0)}
- **Errors**: {session_summary.get("metrics", {}).get("errors", 0)}

## Stage 1: Pattern Analysis

### Identified Patterns
"""

        for pattern in stage1_analysis.get("patterns", []):
            report += f"\n#### {pattern['type'].replace('_', ' ').title()}\n"
            report += f"- **Priority**: {pattern['priority']}\n"
            for key, value in pattern["data"].items():
                report += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        report += """
## Stage 2: Improvement Proposals

### Generated Proposals
"""

        for proposal in stage2_results.get("proposals", []):
            report += f"\n#### {proposal['title']}\n"
            report += f"- **Priority**: {proposal['priority']}\n"
            report += f"- **Type**: {proposal['pattern_type']}\n"
            report += f"- **Labels**: {', '.join(proposal['labels'])}\n"

        if stage2_results.get("created_issues"):
            report += "\n### Created Issues\n"
            for issue in stage2_results["created_issues"]:
                report += f"- [{issue['title']}]({issue['url']}) (#{issue['number']})\n"

        if stage2_results.get("created_prs"):
            report += "\n### Created Pull Requests\n"
            for pr in stage2_results["created_prs"]:
                report += f"- [{pr['title']}]({pr['url']}) (#{pr.get('number', 'pending')})\n"
                report += f"  - Branch: `{pr['branch']}`\n"

        if stage2_results.get("errors"):
            report += "\n### Errors Encountered\n"
            for error in stage2_results["errors"]:
                report += f"- **{error['type']}**: {error.get('title', 'N/A')}\n"
                report += f"  - Error: {error.get('error', 'Unknown error')}\n"

        report += """
## Recommendations

Based on the analysis, consider the following actions:

1. **Review high-priority proposals** for immediate implementation
2. **Investigate recurring patterns** to prevent future issues
3. **Update documentation** based on identified pain points
4. **Consider architectural improvements** for complex workflows

## Next Steps

1. Review and merge created PRs
2. Assign and prioritize created issues
3. Update team processes based on learnings
4. Schedule follow-up analysis after implementations

---
*Report generated by Stage 2 Reflection System*
"""

        return report

    def save_report(self, report: str, session_id: Optional[str] = None) -> Path:
        """Save the report to a file."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        report_file = self.reports_dir / f"reflection_report_{session_id}.md"
        with open(report_file, "w") as f:
            f.write(report)

        return report_file


def main():
    """Main entry point for Stage 2 reflection."""
    import argparse

    parser = argparse.ArgumentParser(description="Stage 2 Reflection - Convert insights to PRs")
    parser.add_argument("stage1_file", help="Path to Stage 1 analysis JSON file")
    parser.add_argument("--create-prs", action="store_true", help="Actually create PRs/issues")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive report")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent.parent.parent
    converter = PatternToPRConverter(project_root)

    # Process Stage 1 output
    stage1_file = Path(args.stage1_file)
    if not stage1_file.exists():
        print(f"Error: Stage 1 file not found: {stage1_file}")
        return 1

    # Convert to PRs
    results = converter.convert_to_prs(stage1_file, create_prs=args.create_prs)

    # Print results
    print("\nStage 2 Reflection Results")
    print("=" * 50)
    print(f"Proposals generated: {len(results['proposals'])}")
    print(f"Issues created: {len(results['created_issues'])}")
    print(f"PRs created: {len(results['created_prs'])}")
    print(f"Errors: {len(results['errors'])}")

    if results["proposals"]:
        print("\nProposed Improvements:")
        for proposal in results["proposals"]:
            print(f"  - [{proposal['priority']}] {proposal['title']}")

    if args.report:
        # Load Stage 1 data for report
        with open(stage1_file, "r") as f:
            stage1_data = json.load(f)

        # Generate report
        reporter = ReflectionReportGenerator(project_root)
        report = reporter.generate_report(
            session_summary=stage1_data,
            stage1_analysis=converter.analyze_stage1_output(stage1_file),
            stage2_results=results,
        )

        # Save report
        report_path = reporter.save_report(report, stage1_data.get("session_id"))
        print(f"\nReport saved to: {report_path}")

    # Save results
    results_file = stage1_file.parent / f"{stage1_file.stem}_stage2.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
