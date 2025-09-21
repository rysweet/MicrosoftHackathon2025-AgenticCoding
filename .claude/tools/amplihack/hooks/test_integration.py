#!/usr/bin/env python3
"""
Integration test to demonstrate the post_edit_format hook in action.
This creates a real file with formatting issues and simulates an Edit.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_python_formatting():
    """Test Python file formatting with black"""
    print("Testing Python file formatting...")

    # Create a poorly formatted Python file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""def  hello(  name,  age  ):
    print(  "Hello "  + name  )
    if   age  >  18:
        return   True
    else:
        return  False


class   Person:
    def   __init__(self,name):
        self.name=name
""")
        temp_file = Path(f.name)

    print(f"Created test file: {temp_file}")
    print("\nOriginal content:")
    print(temp_file.read_text())

    # Simulate Edit tool usage
    hook_path = Path(__file__).parent / "post_edit_format.py"
    tool_use = {
        "toolUse": {
            "name": "Edit",
            "parameters": {"file_path": str(temp_file)},
        }
    }

    # Run the hook
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(tool_use),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout:
        output = json.loads(result.stdout)
        if output.get("message"):
            print(f"\n{output['message']}")

    print("\nFormatted content:")
    print(temp_file.read_text())

    # Clean up
    temp_file.unlink()


def test_json_formatting():
    """Test JSON file formatting with prettier"""
    print("\n" + "=" * 50)
    print("Testing JSON file formatting...")

    # Create a poorly formatted JSON file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"name":"test","nested":{"key1":"value1","key2":"value2"},"array":[1,2,3,4,5]}')
        temp_file = Path(f.name)

    print(f"Created test file: {temp_file}")
    print("\nOriginal content:")
    print(temp_file.read_text())

    # Simulate Edit tool usage
    hook_path = Path(__file__).parent / "post_edit_format.py"
    tool_use = {
        "toolUse": {
            "name": "Edit",
            "parameters": {"file_path": str(temp_file)},
        }
    }

    # Run the hook
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(tool_use),
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout:
        output = json.loads(result.stdout)
        if output.get("message"):
            print(f"\n{output['message']}")

    print("\nFormatted content:")
    print(temp_file.read_text())

    # Clean up
    temp_file.unlink()


def test_environment_control():
    """Test enabling/disabling formatting via environment"""
    print("\n" + "=" * 50)
    print("Testing environment control...")

    import os

    # Test with formatting disabled
    os.environ["CLAUDE_AUTO_FORMAT"] = "false"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def  test( ): pass")
        temp_file = Path(f.name)

    print("\n1. With CLAUDE_AUTO_FORMAT=false:")
    print(f"   Original: {temp_file.read_text()}")

    hook_path = Path(__file__).parent / "post_edit_format.py"
    tool_use = {
        "toolUse": {
            "name": "Edit",
            "parameters": {"file_path": str(temp_file)},
        }
    }

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(tool_use),
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout) if result.stdout else {}
    print(f"   Result: {output or 'No formatting (disabled)'}")
    print(f"   After: {temp_file.read_text()}")

    # Test with formatting enabled
    os.environ["CLAUDE_AUTO_FORMAT"] = "true"

    print("\n2. With CLAUDE_AUTO_FORMAT=true:")
    temp_file.write_text("def  test( ): pass")
    print(f"   Original: {temp_file.read_text()}")

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(tool_use),
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout) if result.stdout else {}
    if output.get("message"):
        print("   Result: Formatted successfully")
    print(f"   After: {temp_file.read_text()}")

    # Clean up
    temp_file.unlink()
    os.environ.pop("CLAUDE_AUTO_FORMAT", None)


if __name__ == "__main__":
    print("=" * 50)
    print("POST-EDIT FORMATTING HOOK - INTEGRATION TEST")
    print("=" * 50)

    test_python_formatting()
    test_json_formatting()
    test_environment_control()

    print("\n" + "=" * 50)
    print("Integration test complete!")
    print("=" * 50)
