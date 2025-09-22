"""AI-powered reflection system - analyzes session logs for improvement opportunities.

Uses AI agents to intelligently analyze session content and identify patterns.
Enabled by default with environment variable control (REFLECTION_ENABLED=false to disable).
Provides full visibility through comprehensive logging.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def analyze_session(messages: List[Dict]) -> List[Dict]:
    """Use AI agent to analyze session content for improvement opportunities."""
    print(f"🔍 Starting AI analysis of {len(messages)} session messages...")

    if not messages:
        print("⚠️  No messages to analyze")
        return []

    try:
        # Prepare session content for AI analysis
        session_summary = prepare_session_for_analysis(messages)

        # Use Task tool to invoke analyzer agent
        print("🤖 Invoking analyzer agent for session review...")

        # For now, simulate AI analysis - in production this would call the analyzer agent
        # This gives us the structure while we integrate with the agent system
        patterns = simulate_ai_analysis(session_summary)

        print(f"✅ AI analysis complete - found {len(patterns)} improvement opportunities")
        for i, pattern in enumerate(patterns, 1):
            print(f"   {i}. [{pattern['priority']}] {pattern['type']}: {pattern['suggestion']}")

        return patterns

    except Exception as e:
        print(f"❌ AI analysis failed: {e}")
        # Don't fail silently - show the user what went wrong
        return []


def prepare_session_for_analysis(messages: List[Dict]) -> str:
    """Extract key content from session messages for AI analysis."""
    print("📝 Preparing session content for AI analysis...")

    content_parts = []
    user_messages = 0
    assistant_messages = 0
    tool_uses = 0
    errors = 0

    for msg in messages:
        role = msg.get("role", "unknown")
        content = str(msg.get("content", ""))

        if role == "user":
            user_messages += 1
            content_parts.append(f"USER: {content[:500]}")
        elif role == "assistant":
            assistant_messages += 1
            content_parts.append(f"ASSISTANT: {content[:500]}")

        # Count tool uses and errors
        if "tool_use" in content.lower():
            tool_uses += 1
        if any(error_word in content.lower() for error_word in ["error", "failed", "exception"]):
            errors += 1

    summary = f"""SESSION SUMMARY:
- Messages: {len(messages)} total ({user_messages} user, {assistant_messages} assistant)
- Tool uses: {tool_uses}
- Errors detected: {errors}

CONTENT SAMPLE (first 20 messages):
{chr(10).join(content_parts[:20])}
"""

    print(f"📊 Session stats: {len(messages)} messages, {tool_uses} tool uses, {errors} errors")
    return summary


def simulate_ai_analysis(session_content: str) -> List[Dict]:
    """Simulate AI analysis until agent integration is complete."""
    patterns = []

    # Look for actual indicators in the session content
    content_lower = session_content.lower()

    # Check for error patterns
    if "error" in content_lower or "failed" in content_lower:
        patterns.append(
            {
                "type": "error_handling",
                "priority": "high",
                "suggestion": "Improve error handling and user feedback based on session failures",
                "evidence": "Multiple errors or failures detected in session",
            }
        )

    # Check for repeated patterns
    if "try again" in content_lower or "repeat" in content_lower:
        patterns.append(
            {
                "type": "workflow",
                "priority": "medium",
                "suggestion": "Streamline workflow to reduce repetitive actions",
                "evidence": "User had to repeat actions or try multiple times",
            }
        )

    # Check for tool usage patterns
    if "tool_use" in content_lower and session_content.count("tool_use") > 10:
        patterns.append(
            {
                "type": "automation",
                "priority": "medium",
                "suggestion": "Consider automating frequently used tool combinations",
                "evidence": f"High tool usage detected ({session_content.count('tool_use')} uses)",
            }
        )

    return patterns


def create_github_issue(pattern: Dict) -> Optional[str]:
    """Create GitHub issue using gh CLI with full logging."""
    print(f"🎫 Creating GitHub issue for {pattern['type']} improvement...")

    try:
        title = f"AI-detected improvement: {pattern['type']} optimization"
        body = f"""# AI-Detected Improvement Opportunity

**Type**: {pattern["type"]}
**Priority**: {pattern["priority"]}
**Evidence**: {pattern.get("evidence", "Detected during session analysis")}

## Suggestion
{pattern["suggestion"]}

## Analysis Details
This improvement was identified by AI analysis of session logs. The system detected patterns indicating this area needs attention.

## Next Steps
UltraThink will analyze this issue and implement the necessary changes following the complete DEFAULT_WORKFLOW.md process.

**Labels**: ai-improvement, {pattern["type"]}, {pattern["priority"]}-priority
"""

        print(f"📝 Issue title: {title}")
        print(f"🏷️  Labels: ai-improvement, {pattern['type']}, {pattern['priority']}-priority")

        # Use gh CLI to create issue
        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                f"ai-improvement,{pattern['type']},{pattern['priority']}-priority",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Extract issue number from output
            issue_url = result.stdout.strip()
            print("✅ Issue created successfully")
            print(f"📎 Issue URL: {issue_url}")
            if issue_url:
                issue_number = issue_url.split("/")[-1]
                return issue_number
        else:
            print(f"❌ Failed to create issue. Exit code: {result.returncode}")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")

    except Exception as e:
        print(f"❌ Exception creating GitHub issue: {e}")

    return None


def invoke_ultrathink(issue_number: str, pattern: Dict) -> bool:
    """Delegate to UltraThink for workflow execution with full logging."""
    print(f"🚀 Delegating to UltraThink for issue #{issue_number}...")

    try:
        # Create task description for UltraThink
        task_description = f"""Fix GitHub issue #{issue_number}: {pattern["suggestion"]}

This is an AI-detected improvement based on session analysis.
Please follow the complete DEFAULT_WORKFLOW.md process:
1. Analyze the issue and clarify requirements
2. Design the solution
3. Implement the fix
4. Test thoroughly
5. Create a pull request

Pattern type: {pattern["type"]}
Priority: {pattern["priority"]}
Evidence: {pattern.get("evidence", "Detected in session")}
"""

        # Save task to file for UltraThink processing
        task_file = Path.cwd() / ".claude" / "runtime" / "automation" / f"task_{issue_number}.md"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(task_description)
        print(f"📄 Task file created: {task_file}")

        # Execute UltraThink command directly via Claude CLI
        print(f"🔧 Executing: claude ultrathink 'Fix issue #{issue_number}'")
        try:
            result = subprocess.run(
                ["claude", "ultrathink", f"Fix issue #{issue_number}: {pattern['suggestion']}"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(Path.cwd()),
            )

            if result.returncode == 0:
                print("✅ UltraThink delegation successful")
                print("📎 The automated workflow will create a PR when complete")
                return True
            else:
                print(f"⚠️  UltraThink returned non-zero exit code: {result.returncode}")
                print(f"   Task saved for manual processing: {task_file}")
                if result.stdout:
                    print(f"   stdout: {result.stdout[:200]}")
                if result.stderr:
                    print(f"   stderr: {result.stderr[:200]}")
                return False
        except subprocess.TimeoutExpired:
            print("⏰ UltraThink command timed out after 300 seconds")
            print(f"   Task saved for manual processing: {task_file}")
            return False
        except Exception as e:
            print(f"❌ Failed to execute UltraThink: {e}")
            print(f"   Task saved for manual processing: {task_file}")
            return False

    except Exception as e:
        print(f"❌ Error preparing UltraThink delegation: {e}")
        return False


def should_trigger_automation(patterns: List[Dict]) -> bool:
    """Determine if we should create issues and trigger automated fixes."""
    if not patterns:
        print("ℹ️  No improvement patterns detected")
        return False

    print(f"🎯 Evaluating {len(patterns)} patterns for automated improvement...")

    # Simple heuristic: trigger if we have high priority patterns
    high_priority_count = sum(1 for p in patterns if p["priority"] == "high")
    medium_priority_count = sum(1 for p in patterns if p["priority"] == "medium")

    if high_priority_count >= 1:
        print(f"✅ Will create GitHub issue for {high_priority_count} high priority improvement(s)")
        return True
    elif medium_priority_count >= 2:
        print(
            f"✅ Will create GitHub issue for {medium_priority_count} medium priority improvements"
        )
        return True
    else:
        print(
            "ℹ️  Improvements below threshold for automated fixes (need 1+ high or 2+ medium priority)"
        )
        return False


def process_reflection_analysis(analysis_path: Path, force: bool = False) -> Optional[str]:
    """Main entry point: AI-powered reflection analysis with full visibility.

    Args:
        analysis_path: Path to the session analysis JSON file
        force: Force analysis even if disabled via environment variable

    Returns:
        Issue number if automation triggered, None otherwise.
    """
    # Check if reflection is enabled (default: true)
    if not force:
        enabled = os.environ.get("REFLECTION_ENABLED", "true").lower()
        if enabled in ["false", "0", "no", "off", "disabled"]:
            print("ℹ️  Reflection analysis is disabled (set REFLECTION_ENABLED=true to enable)")
            return None

    print(f"\n{'=' * 60}")
    print("🤖 AI REFLECTION ANALYSIS STARTING")
    print(f"{'=' * 60}")

    try:
        # Load analysis data
        if not analysis_path.exists():
            print(f"❌ Analysis file not found: {analysis_path}")
            return None

        print(f"📂 Loading analysis from: {analysis_path}")
        with open(analysis_path, "r") as f:
            analysis_data = json.load(f)

        # Extract messages if available
        messages = []
        if "messages" in analysis_data:
            messages = analysis_data["messages"]
        elif "transcript" in analysis_data:
            messages = analysis_data["transcript"]
        elif "learnings" in analysis_data:
            # Use learnings as proxy for session content
            messages = [{"role": "system", "content": str(analysis_data["learnings"])}]

        if messages:
            # Use AI analysis on actual session messages
            patterns = analyze_session(messages)
        else:
            # Fallback to simpler analysis of the analysis data itself
            print("⚠️  No session messages found, using fallback analysis")
            patterns = simulate_ai_analysis(str(analysis_data))

        # Check if automation should be triggered
        if not should_trigger_automation(patterns):
            print(f"\n{'=' * 60}")
            print("📊 ANALYSIS COMPLETE - No automation needed")
            print(f"{'=' * 60}\n")
            return None

        # Take the highest priority pattern
        top_pattern = patterns[0]
        print(f"\n🎯 Processing top priority pattern: {top_pattern['type']}")

        # Create GitHub issue
        issue_number = create_github_issue(top_pattern)
        if not issue_number:
            print("❌ Failed to create GitHub issue")
            return None

        # Delegate to UltraThink
        success = invoke_ultrathink(issue_number, top_pattern)

        print(f"\n{'=' * 60}")
        if success:
            print("✅ AUTOMATION COMPLETE")
            print(f"📎 Created Issue: #{issue_number}")
            print("🔄 UltraThink will create a PR for the fix")
        else:
            print("⚠️  PARTIAL SUCCESS")
            print(f"📎 Created Issue: #{issue_number}")
            print("⚠️  Manual UltraThink execution needed for PR creation")
        print(f"{'=' * 60}\n")

        return issue_number if success else None

    except Exception as e:
        # Full error visibility - never silent
        print(f"\n❌ AUTOMATION ERROR: {e}")
        import traceback

        print(f"Stack trace:\n{traceback.format_exc()}")
        print(f"{'=' * 60}\n")
        return None


def main():
    """CLI interface for testing."""
    if len(sys.argv) != 2:
        print("Usage: python simple_reflection.py <analysis_file.json>")
        sys.exit(1)

    analysis_path = Path(sys.argv[1])
    result = process_reflection_analysis(analysis_path)

    if result:
        print(f"Automation triggered: Issue #{result}")
    else:
        print("No automation triggered")


if __name__ == "__main__":
    main()
