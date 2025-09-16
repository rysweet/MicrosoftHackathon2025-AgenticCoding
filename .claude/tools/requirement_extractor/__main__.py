#!/usr/bin/env python3
"""
Simplified requirements extraction tool that trusts Claude to do the analysis.

Philosophy: Code provides structure, Claude provides intelligence.
We just need to clearly communicate the task, not orchestrate every detail.
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point - just parse args and provide instructions"""
    parser = argparse.ArgumentParser(
        description="Extract functional requirements from codebases using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool asks Claude to analyze your codebase and extract requirements.
It trusts Claude's intelligence rather than trying to orchestrate every detail.

Examples:
  python -m requirement_extractor /path/to/project --output requirements.md
  python -m requirement_extractor . -o reqs.md
        """,
    )

    parser.add_argument("project_path", help="Path to the project directory to analyze")

    parser.add_argument("--output", "-o", default="requirements.md", help="Output file path (default: requirements.md)")

    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json", "yaml"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Validate project path
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        return 1

    if not project_path.is_dir():
        print(f"Error: Project path is not a directory: {project_path}", file=sys.stderr)
        return 1

    # Display the task
    print("=" * 60)
    print("Requirements Extraction Tool")
    print("=" * 60)
    print(f"Project: {project_path}")
    print(f"Output: {args.output} ({args.format})")
    print("=" * 60)
    print()

    # The actual instruction for Claude
    instruction = f"""
Please analyze the codebase at {project_path} and extract functional requirements.

TASK:
1. Explore the project structure to understand the codebase
2. Identify major functional modules and components
3. Extract what each module/component does (functionality, not implementation)
4. Organize requirements by functional category
5. Save the results to: {args.output}

REQUIREMENTS FORMAT:
- Use standard REQ-XXX-NNN identifiers (e.g., REQ-MEM-001 for memory module)
- Each requirement should include:
  * ID and Title
  * Clear description of WHAT the system does
  * Category (API, Data, UI, Security, Integration, etc.)
  * Priority (High/Medium/Low)
  * Brief evidence or rationale

OUTPUT FORMAT: {args.format}

FOCUS ON:
- User-facing functionality
- Business logic and rules
- Data processing and transformations
- API endpoints and interfaces
- Integration points
- Security and access control
- Performance-critical operations

AVOID:
- Implementation details
- Technology stack specifics
- Code structure descriptions
- How things are coded

Please be comprehensive and analyze all modules in the project.
"""

    print("INSTRUCTION FOR CLAUDE:")
    print("-" * 60)
    print(instruction)
    print("-" * 60)
    print()
    print("Claude will now analyze the codebase and extract requirements.")
    print("This may take a few minutes depending on the project size.")
    print()

    # In a real implementation, this is where we'd invoke Claude
    # For now, we just print the instructions
    print("Note: In production, this would invoke Claude directly.")
    print("For now, please copy the instruction above and run it manually.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
