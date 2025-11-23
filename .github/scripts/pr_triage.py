#!/usr/bin/env python3
"""Sophisticated PR triage using Claude CLI.

This script validates PRs against workflow compliance requirements:
- Checks that Steps 11-12 of DEFAULT_WORKFLOW.md are completed
- Applies appropriate labels (priority, complexity)
- Detects unrelated changes
- Returns PR to draft and spawns auto mode fix if issues found

Uses Claude CLI directly for AI-powered analysis.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).parent.parent.parent


class PRTriageValidator:
    """Validates PR compliance using Claude CLI."""

    def __init__(self, pr_number: int):
        """Initialize validator.

        Args:
            pr_number: GitHub PR number
        """
        self.pr_number = pr_number
        self.log_dir = REPO_ROOT / ".claude" / "runtime" / "logs" / f"pr-triage-{pr_number}"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, msg: str, level: str = "INFO") -> None:
        """Log message to console and file.

        Args:
            msg: Message to log
            level: Log level
        """
        log_msg = f"[{time.strftime('%H:%M:%S')}] [{level}] [PR-{self.pr_number}] {msg}"
        print(log_msg)

        log_file = self.log_dir / "triage.log"
        with open(log_file, "a") as f:
            f.write(log_msg + "\n")

    def run_claude(self, prompt: str, process_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Run Claude CLI with prompt and return result.

        Args:
            prompt: Prompt to send to Claude
            process_id: Process identifier for logging
            timeout: Timeout in seconds

        Returns:
            Dictionary with exit_code, output, stderr
        """
        self.log(f"Running Claude process: {process_id}")

        try:
            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", "-p", prompt],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "exit_code": result.returncode,
                "output": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            self.log(f"Process {process_id} timed out after {timeout}s", level="WARNING")
            return {"exit_code": -1, "output": "", "stderr": "Timeout"}
        except Exception as e:
            self.log(f"Process {process_id} failed: {e}", level="ERROR")
            return {"exit_code": -1, "output": "", "stderr": str(e)}

    def get_pr_data(self) -> Dict[str, Any]:
        """Fetch PR data using gh CLI.

        Returns:
            PR data dictionary with title, body, files, comments, etc.
        """
        # Fetch PR details
        pr_json = subprocess.check_output(
            [
                "gh",
                "pr",
                "view",
                str(self.pr_number),
                "--json",
                "title,body,headRefName,baseRefName,author,files,comments,reviews",
            ],
            text=True,
        )
        pr_data = json.loads(pr_json)

        # Fetch diff
        diff = subprocess.check_output(["gh", "pr", "diff", str(self.pr_number)], text=True)
        pr_data["diff"] = diff

        return pr_data

    def validate_workflow_compliance(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if PR completed Steps 11-12 of workflow.

        Args:
            pr_data: PR data dictionary

        Returns:
            Validation result with compliance status and details
        """
        prompt = f"""Analyze this PR for workflow compliance with DEFAULT_WORKFLOW.md.

**CRITICAL REQUIREMENTS:**

Step 11: Review the PR
- Must have comprehensive code review comment posted
- Security review must be performed
- Code quality and standards checked
- Philosophy compliance verified
- Test coverage verified
- No TODOs, stubs, or swallowed exceptions

Step 12: Implement Review Feedback
- All review comments must be addressed
- Each comment should have a response
- Changes pushed to address feedback
- Tests still passing

**PR Data:**
Title: {pr_data["title"]}
Author: {pr_data["author"]["login"]}
Branch: {pr_data["headRefName"]} -> {pr_data["baseRefName"]}

Body:
{pr_data["body"]}

Comments ({len(pr_data["comments"])}):
{self._format_comments(pr_data["comments"])}

Reviews ({len(pr_data["reviews"])}):
{self._format_reviews(pr_data["reviews"])}

**RESPOND IN JSON FORMAT:**
{{
    "step11_completed": true/false,
    "step11_evidence": "description of review evidence or missing items",
    "step12_completed": true/false,
    "step12_evidence": "description of feedback implementation or missing items",
    "overall_compliant": true/false,
    "blocking_issues": ["list", "of", "issues"],
    "recommendations": ["list", "of", "recommendations"]
}}
"""

        result = self.run_claude(prompt, "workflow-compliance-check", timeout=300)

        if result["exit_code"] != 0:
            return {
                "overall_compliant": False,
                "error": f"Validation failed: {result['stderr']}",
            }

        # Extract JSON from output
        return self._extract_json(result["output"])

    def detect_priority_complexity(self, pr_data: Dict[str, Any]) -> Dict[str, str]:
        """Detect appropriate priority and complexity labels.

        Args:
            pr_data: PR data dictionary

        Returns:
            Dictionary with priority and complexity labels
        """
        prompt = f"""Analyze this PR to determine priority and complexity.

**PR Data:**
Title: {pr_data["title"]}
Body:
{pr_data["body"]}

Files Changed: {len(pr_data["files"])}
File List:
{self._format_files(pr_data["files"])}

Diff Preview (first 5000 chars):
{pr_data["diff"][:5000]}

**Priority Levels:**
- CRITICAL: Security issues, data loss, system down
- HIGH: Major bugs, important features, significant impact
- MEDIUM: Normal features, moderate bugs, improvements
- LOW: Minor fixes, documentation, cleanup

**Complexity Levels:**
- SIMPLE: Single file, < 50 lines, straightforward logic
- MODERATE: Few files, < 200 lines, some complexity
- COMPLEX: Multiple files, > 200 lines, intricate logic
- VERY_COMPLEX: System-wide changes, architectural shifts

**RESPOND IN JSON FORMAT:**
{{
    "priority": "CRITICAL/HIGH/MEDIUM/LOW",
    "priority_reasoning": "explanation",
    "complexity": "SIMPLE/MODERATE/COMPLEX/VERY_COMPLEX",
    "complexity_reasoning": "explanation"
}}
"""

        result = self.run_claude(prompt, "priority-complexity-detection", timeout=300)

        if result["exit_code"] != 0:
            return {"priority": "MEDIUM", "complexity": "MODERATE", "error": result["stderr"]}

        return self._extract_json(result["output"])

    def detect_unrelated_changes(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if PR contains unrelated changes.

        Args:
            pr_data: PR data dictionary

        Returns:
            Dictionary with unrelated changes detection results
        """
        prompt = f"""Analyze this PR to detect unrelated changes.

A PR should have a single, focused purpose. Unrelated changes are:
- Changes to files outside the scope of the PR's stated purpose
- Mixed refactoring with new features
- Unrelated bug fixes bundled together
- Documentation updates unrelated to the code changes

**PR Data:**
Title: {pr_data["title"]}
Body:
{pr_data["body"]}

Files Changed:
{self._format_files(pr_data["files"])}

Diff (first 10000 chars):
{pr_data["diff"][:10000]}

**RESPOND IN JSON FORMAT:**
{{
    "has_unrelated_changes": true/false,
    "unrelated_files": ["list", "of", "file", "paths"],
    "primary_purpose": "description of main PR purpose",
    "unrelated_purposes": ["list", "of", "unrelated", "changes"],
    "recommendation": "should these be split into separate PRs?"
}}
"""

        result = self.run_claude(prompt, "unrelated-changes-detection", timeout=300)

        if result["exit_code"] != 0:
            return {"has_unrelated_changes": False, "error": result["stderr"]}

        return self._extract_json(result["output"])

    def generate_triage_report(
        self,
        pr_data: Dict[str, Any],
        compliance: Dict[str, Any],
        labels: Dict[str, str],
        unrelated: Dict[str, Any],
    ) -> str:
        """Generate comprehensive triage report.

        Args:
            pr_data: PR data
            compliance: Workflow compliance results
            labels: Priority and complexity labels
            unrelated: Unrelated changes detection

        Returns:
            Markdown report
        """
        report_parts = [
            "## 🤖 PM Architect PR Triage Analysis",
            "",
            f"**PR**: #{self.pr_number}",
            f"**Title**: {pr_data['title']}",
            f"**Author**: @{pr_data['author']['login']}",
            f"**Branch**: `{pr_data['headRefName']}` → `{pr_data['baseRefName']}`",
            "",
            "---",
            "",
        ]

        # Workflow Compliance
        report_parts.extend(
            [
                "### ✅ Workflow Compliance (Steps 11-12)",
                "",
            ]
        )

        if compliance.get("overall_compliant"):
            report_parts.extend(
                [
                    "✅ **COMPLIANT** - PR meets workflow requirements",
                    "",
                    f"**Step 11 (Review)**: {'✅ Completed' if compliance.get('step11_completed') else '❌ Incomplete'}",
                    f"- {compliance.get('step11_evidence', 'N/A')}",
                    "",
                    f"**Step 12 (Feedback)**: {'✅ Completed' if compliance.get('step12_completed') else '❌ Incomplete'}",
                    f"- {compliance.get('step12_evidence', 'N/A')}",
                    "",
                ]
            )
        else:
            report_parts.extend(
                [
                    "❌ **NON-COMPLIANT** - PR needs workflow completion",
                    "",
                    f"**Step 11 (Review)**: {'✅ Completed' if compliance.get('step11_completed') else '❌ Incomplete'}",
                    f"- {compliance.get('step11_evidence', 'N/A')}",
                    "",
                    f"**Step 12 (Feedback)**: {'✅ Completed' if compliance.get('step12_completed') else '❌ Incomplete'}",
                    f"- {compliance.get('step12_evidence', 'N/A')}",
                    "",
                    "**Blocking Issues:**",
                ]
            )
            for issue in compliance.get("blocking_issues", []):
                report_parts.append(f"- {issue}")
            report_parts.append("")

        # Priority and Complexity
        report_parts.extend(
            [
                "### 🏷️ Classification",
                "",
                f"**Priority**: `{labels.get('priority', 'MEDIUM')}`",
                f"- {labels.get('priority_reasoning', 'N/A')}",
                "",
                f"**Complexity**: `{labels.get('complexity', 'MODERATE')}`",
                f"- {labels.get('complexity_reasoning', 'N/A')}",
                "",
            ]
        )

        # Unrelated Changes
        report_parts.extend(
            [
                "### 🔍 Change Scope Analysis",
                "",
            ]
        )

        if unrelated.get("has_unrelated_changes"):
            report_parts.extend(
                [
                    "⚠️ **UNRELATED CHANGES DETECTED**",
                    "",
                    f"**Primary Purpose**: {unrelated.get('primary_purpose', 'N/A')}",
                    "",
                    "**Unrelated Changes:**",
                ]
            )
            for purpose in unrelated.get("unrelated_purposes", []):
                report_parts.append(f"- {purpose}")
            report_parts.extend(
                [
                    "",
                    "**Affected Files:**",
                ]
            )
            for file_path in unrelated.get("unrelated_files", []):
                report_parts.append(f"- `{file_path}`")
            report_parts.extend(
                [
                    "",
                    f"**Recommendation**: {unrelated.get('recommendation', 'N/A')}",
                    "",
                ]
            )
        else:
            report_parts.extend(
                [
                    "✅ **FOCUSED CHANGES** - All changes are related to PR purpose",
                    "",
                    f"**Purpose**: {unrelated.get('primary_purpose', 'N/A')}",
                    "",
                ]
            )

        # Recommendations
        if compliance.get("recommendations"):
            report_parts.extend(
                [
                    "### 💡 Recommendations",
                    "",
                ]
            )
            for rec in compliance.get("recommendations", []):
                report_parts.append(f"- {rec}")
            report_parts.append("")

        # Statistics
        report_parts.extend(
            [
                "---",
                "",
                "### 📊 Statistics",
                "",
                f"- **Files Changed**: {len(pr_data['files'])}",
                f"- **Comments**: {len(pr_data['comments'])}",
                f"- **Reviews**: {len(pr_data['reviews'])}",
                "",
            ]
        )

        # Footer
        report_parts.extend(
            [
                "---",
                "",
                "*🤖 Generated by PM Architect automation using Claude Agent SDK*",
                "",
            ]
        )

        return "\n".join(report_parts)

    def apply_labels(self, labels: Dict[str, str]) -> None:
        """Apply priority and complexity labels to PR.

        Args:
            labels: Dictionary with priority and complexity
        """
        priority = labels.get("priority", "MEDIUM")
        complexity = labels.get("complexity", "MODERATE")

        label_names = [
            f"priority:{priority.lower()}",
            f"complexity:{complexity.lower()}",
        ]

        for label in label_names:
            try:
                subprocess.run(
                    ["gh", "pr", "edit", str(self.pr_number), "--add-label", label],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                self.log(
                    f"Warning: Failed to add label {label}: {e.stderr.decode()}",
                    level="WARNING",
                )

    def return_to_draft(self) -> None:
        """Convert PR back to draft status."""
        try:
            subprocess.run(
                ["gh", "pr", "ready", str(self.pr_number), "--undo"],
                check=True,
                capture_output=True,
            )
            self.log(f"Returned PR #{self.pr_number} to draft status")
        except subprocess.CalledProcessError as e:
            self.log(
                f"Warning: Failed to return to draft: {e.stderr.decode()}",
                level="WARNING",
            )

    def spawn_auto_fix(self, compliance: Dict[str, Any]) -> None:
        """Spawn auto mode to fix workflow compliance issues.

        Args:
            compliance: Compliance validation results
        """
        issues = compliance.get("blocking_issues", [])
        if not issues:
            return

        fix_prompt = f"""Fix workflow compliance issues in PR #{self.pr_number}.

**Blocking Issues:**
{chr(10).join(f"- {issue}" for issue in issues)}

**Required Actions:**
1. Complete Step 11 (Review the PR):
   - Post comprehensive code review
   - Perform security review
   - Verify code quality and standards
   - Check philosophy compliance
   - Verify test coverage

2. Complete Step 12 (Implement Review Feedback):
   - Address all review comments
   - Push updates to PR
   - Respond to comments
   - Ensure tests still pass

Follow the DEFAULT_WORKFLOW.md process exactly.
"""

        self.log("Spawning auto mode to fix compliance issues...")

        # Run fix process (may timeout - that's OK)
        result = self.run_claude(fix_prompt, f"auto-fix-pr-{self.pr_number}", timeout=1800)

        if result["exit_code"] == 0:
            self.log("Auto-fix completed successfully")
        else:
            self.log(f"Auto-fix failed: {result['stderr']}", level="ERROR")

    def post_report(self, report: str) -> None:
        """Post triage report as PR comment.

        Args:
            report: Markdown report content
        """
        # Write report to file
        report_file = self.log_dir / "triage_report.md"
        report_file.write_text(report)

        # Post to PR
        try:
            subprocess.run(
                [
                    "gh",
                    "pr",
                    "comment",
                    str(self.pr_number),
                    "--body-file",
                    str(report_file),
                ],
                check=True,
                capture_output=True,
            )
            self.log(f"Posted triage report to PR #{self.pr_number}")
        except subprocess.CalledProcessError as e:
            self.log(f"Error posting report: {e.stderr.decode()}", level="ERROR")

    def _format_comments(self, comments: List[Dict[str, Any]]) -> str:
        """Format PR comments for analysis."""
        if not comments:
            return "(No comments)"

        lines = []
        for i, comment in enumerate(comments[:10], 1):  # Limit to 10
            author = comment.get("author", {}).get("login", "unknown")
            body = comment.get("body", "")[:200]  # Truncate long comments
            lines.append(f"{i}. @{author}: {body}")

        if len(comments) > 10:
            lines.append(f"... and {len(comments) - 10} more")

        return "\n".join(lines)

    def _format_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """Format PR reviews for analysis."""
        if not reviews:
            return "(No reviews)"

        lines = []
        for i, review in enumerate(reviews, 1):
            author = review.get("author", {}).get("login", "unknown")
            state = review.get("state", "UNKNOWN")
            body = review.get("body", "")[:200]
            lines.append(f"{i}. @{author} ({state}): {body}")

        return "\n".join(lines)

    def _format_files(self, files: List[Dict[str, Any]]) -> str:
        """Format file list for analysis."""
        if not files:
            return "(No files)"

        lines = []
        for file_data in files[:50]:  # Limit to 50 files
            path = file_data.get("path", "unknown")
            additions = file_data.get("additions", 0)
            deletions = file_data.get("deletions", 0)
            lines.append(f"- {path} (+{additions}/-{deletions})")

        if len(files) > 50:
            lines.append(f"... and {len(files) - 50} more")

        return "\n".join(lines)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Claude output.

        Args:
            text: Full text output from Claude

        Returns:
            Parsed JSON dictionary
        """
        # Look for JSON blocks

        # Try to find JSON in code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find raw JSON
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        # Fallback: empty dict
        self.log("Warning: Could not extract JSON from output", level="WARNING")
        return {}


def main():
    """Main entry point for PR triage."""
    # Get PR number from environment
    pr_number = int(os.environ.get("PR_NUMBER", "0"))
    if not pr_number:
        print("Error: PR_NUMBER environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Create validator
    validator = PRTriageValidator(pr_number)

    try:
        # Fetch PR data
        validator.log("Fetching PR data...")
        pr_data = validator.get_pr_data()

        # Run validations
        validator.log("Validating workflow compliance...")
        compliance = validator.validate_workflow_compliance(pr_data)

        validator.log("Detecting priority and complexity...")
        labels = validator.detect_priority_complexity(pr_data)

        validator.log("Checking for unrelated changes...")
        unrelated = validator.detect_unrelated_changes(pr_data)

        # Generate report
        validator.log("Generating triage report...")
        report = validator.generate_triage_report(pr_data, compliance, labels, unrelated)

        # Apply labels
        validator.log("Applying labels...")
        validator.apply_labels(labels)

        # Post report
        validator.log("Posting triage report...")
        validator.post_report(report)

        # Handle non-compliance
        if not compliance.get("overall_compliant"):
            validator.log(
                "PR is non-compliant, returning to draft and spawning auto-fix...",
                level="WARNING",
            )
            validator.return_to_draft()
            validator.spawn_auto_fix(compliance)

        validator.log("PR triage completed successfully")

    except Exception as e:
        validator.log(f"Fatal error: {e}", level="ERROR")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
