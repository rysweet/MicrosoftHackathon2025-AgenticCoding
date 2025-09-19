#!/usr/bin/env python3
"""
Simple workflow runner that executes steps from workflow configuration.
Each step is just a prompt sent to the appropriate agent or command.
"""

import sys
from pathlib import Path

import yaml


def load_workflow(config_path=None):
    """Load workflow configuration from YAML file"""
    if not config_path:
        config_path = Path(__file__).parent / "default-workflow.yaml"

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def execute_step(step, context):
    """Execute a single workflow step"""
    print(f"\n{'=' * 60}")
    print(f"Step {step['id']}: {step['name']}")
    print(f"{'=' * 60}")

    # Format the prompt with context
    prompt = step["prompt"].format(**context)

    if "agent" in step:
        print(f"Agent: {step['agent']}")
        print(f"Prompt:\n{prompt}")
        # In real implementation, call the agent via Task tool

    elif "agents" in step:
        print(f"Agents: {', '.join(step['agents'])}")
        print(f"Prompt:\n{prompt}")
        # In real implementation, call multiple agents in parallel

    elif "command" in step:
        print(f"Command: {step['command']}")
        print(f"Instructions:\n{prompt}")
        # In real implementation, execute the command

    # Simulate user continuing
    input("\nPress Enter to continue to next step...")
    return True


def run_workflow(task, config_path=None):
    """Run the complete workflow for a given task"""
    workflow = load_workflow(config_path)

    print(f"\nStarting: {workflow['workflow']['name']}")
    print(f"Task: {task}\n")

    # Context that gets passed between steps
    context = {
        "task": task,
        "refined_task": task,  # Will be updated by step 1
        "issue_number": "999",  # Will be set by step 2
        "brief_description": "feature",  # Will be extracted from task
        "architecture": "TBD",  # Will be set by step 4
        "test_files": "tests/",  # Will be set by step 4
        "review_comments": "TBD",  # Will be set by step 10
    }

    # Check if user wants to see/edit workflow on first run
    if workflow["workflow"]["configuration"]["show_on_first_run"]:
        print("This is the default workflow. Would you like to review/edit it?")
        response = input("(y/N): ").lower()
        if response == "y":
            print(f"\nWorkflow configuration is at: {config_path}")
            print("Edit it and restart when ready.\n")
            return

    # Execute each step
    for i, step in enumerate(workflow["workflow"]["steps"], 1):
        print(f"\n[Step {i}/{len(workflow['workflow']['steps'])}]")

        success = execute_step(step, context)

        if not success:
            if workflow["workflow"]["configuration"]["error_handling"] == "pause":
                print("\nStep failed. Workflow paused.")
                print("Fix the issue and resume.")
                return
            elif workflow["workflow"]["configuration"]["error_handling"] == "retry":
                print("\nRetrying step...")
                success = execute_step(step, context)
                if not success:
                    print("\nRetry failed. Stopping workflow.")
                    return
            else:  # fail
                print("\nStep failed. Stopping workflow.")
                return

    print("\n" + "=" * 60)
    print("✅ Workflow completed successfully!")
    print("PR is ready for review and merge.")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_workflow.py '<task description>'")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    run_workflow(task)
