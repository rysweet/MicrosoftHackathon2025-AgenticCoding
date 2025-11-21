#!/usr/bin/env python3
"""
/transcripts command - Save and restore conversation context from transcripts
Implements amplihack-style context preservation and restoration capabilities.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Clean import setup - use robust path detection
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
try:
    from amplihack.utils.paths import FrameworkPathResolver

    project_root = FrameworkPathResolver.find_framework_root()
    if project_root is None:
        raise RuntimeError(
            "Could not find project root. Ensure .claude directory exists or set AMPLIHACK_ROOT environment variable."
        )
except ImportError:
    # Fallback for local development - try relative path
    project_root = Path(__file__).resolve().parents[2]
    if not (project_root / ".claude").exists():
        raise RuntimeError(
            "Could not find project root with .claude directory. Please ensure you are running from the correct location."
        )

sys.path.insert(0, str(project_root / ".claude" / "tools" / "amplihack"))


def list_available_sessions() -> List[str]:
    """List available session transcripts."""
    logs_dir = project_root / ".claude" / "runtime" / "logs"
    if not logs_dir.exists():
        return []

    sessions = []
    for session_dir in logs_dir.iterdir():
        if session_dir.is_dir() and (session_dir / "CONVERSATION_TRANSCRIPT.md").exists():
            sessions.append(session_dir.name)

    return sorted(sessions, reverse=True)  # Most recent first


def get_session_summary(session_id: str) -> Dict[str, str]:
    """Get summary information for a session."""
    session_dir = project_root / ".claude" / "runtime" / "logs" / session_id

    summary = {
        "session_id": session_id,
        "transcript_exists": False,
        "original_request_exists": False,
        "target": "Unknown",
        "message_count": 0,
        "timestamp": "Unknown",
    }

    # Check for transcript
    transcript_file = session_dir / "CONVERSATION_TRANSCRIPT.md"
    if transcript_file.exists():
        summary["transcript_exists"] = True
        try:
            content = transcript_file.read_text()
            # Extract message count
            if "**Messages**:" in content:
                line = [
                    msg_line for msg_line in content.split("\n") if "**Messages**:" in msg_line
                ][0]
                summary["message_count"] = int(line.split(":")[-1].strip())
        except (ValueError, IndexError, OSError):
            pass

    # Check for original request
    original_request_file = session_dir / "original_request.json"
    if original_request_file.exists():
        summary["original_request_exists"] = True
        try:
            with open(original_request_file) as f:
                data = json.load(f)
                summary["target"] = data.get("target", "Unknown")
                summary["timestamp"] = data.get("timestamp", "Unknown")
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    return summary


def display_session_list(sessions: List[str]) -> None:
    """Display formatted list of available sessions."""
    if not sessions:
        print("🔍 No conversation transcripts found")
        print("   Transcripts are automatically created when PreCompact hook triggers")
        return

    print(f"📋 Available Conversation Transcripts ({len(sessions)} sessions)")
    print("━" * 80)

    for i, session_id in enumerate(sessions[:10], 1):  # Show latest 10
        summary = get_session_summary(session_id)

        # Format timestamp
        try:
            if summary["timestamp"] != "Unknown":
                ts = datetime.fromisoformat(summary["timestamp"].replace("Z", "+00:00"))
                time_str = ts.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "Unknown time"
        except (ValueError, KeyError, AttributeError):
            time_str = "Unknown time"

        # Status indicators
        status = []
        if summary["transcript_exists"]:
            status.append(f"📄 {summary['message_count']} msgs")
        if summary["original_request_exists"]:
            status.append("🎯 original req")

        status_str = " | ".join(status) if status else "❌ incomplete"

        print(f"{i:2d}. {session_id}")
        print(f"    🕒 {time_str}")
        print(f"    🎯 {summary['target'][:60]}{'...' if len(summary['target']) > 60 else ''}")
        print(f"    📊 {status_str}")
        print()


def restore_session_context(session_id: str) -> None:
    """Restore and display context from a specific session."""
    session_dir = project_root / ".claude" / "runtime" / "logs" / session_id

    if not session_dir.exists():
        print(f"❌ Session not found: {session_id}")
        return

    print(f"🔄 Restoring Context from Session: {session_id}")
    print("━" * 80)

    # Display original request if available
    original_request_file = session_dir / "ORIGINAL_REQUEST.md"
    if original_request_file.exists():
        print("🎯 ORIGINAL USER REQUEST")
        print("━" * 40)
        content = original_request_file.read_text()
        # Skip the header and show the content
        lines = content.split("\n")
        in_request = False
        for line in lines:
            if line.startswith("## Raw Request"):
                in_request = True
                continue
            if line.startswith("## ") and in_request:
                break
            if in_request and not line.startswith("```"):
                print(line)
        print()

    # Display conversation summary
    transcript_file = session_dir / "CONVERSATION_TRANSCRIPT.md"
    if transcript_file.exists():
        print("💬 CONVERSATION SUMMARY")
        print("━" * 40)
        content = transcript_file.read_text()

        # Extract key information
        lines = content.split("\n")
        for line in lines[:10]:  # Show header info
            if line.startswith("**"):
                print(line)

        print()
        print("📄 Full transcript available at:")
        print(f"   {transcript_file}")
        print()

    # Display compaction events if any
    compaction_file = session_dir / "compaction_events.json"
    if compaction_file.exists():
        try:
            with open(compaction_file) as f:
                events = json.load(f)
            print(f"🔄 COMPACTION EVENTS ({len(events)})")
            print("━" * 40)
            for event in events[-3:]:  # Show last 3 events
                trigger = event.get("compaction_trigger", "unknown")
                timestamp = event.get("timestamp", "")
                msg_count = event.get("messages_exported", 0)
                print(f"   📅 {timestamp[:19]}")
                print(f"   🔄 Trigger: {trigger}")
                print(f"   💬 Exported: {msg_count} messages")
                print()
        except (KeyError, IndexError, TypeError):
            pass

    print("✅ Context restoration complete!")
    print("   Original requirements have been preserved and can be referenced by agents.")


def get_current_session_id() -> str:
    """Get or generate the current session ID.

    Attempts to find the current session ID from:
    1. Runtime environment variables
    2. Latest session directory
    3. Generate new session ID from timestamp

    Returns:
        Current session ID string in format YYYYMMDD_HHMMSS
    """
    import os

    # Try environment variable first (if set by Claude Code)
    env_session = os.environ.get("AMPLIHACK_SESSION_ID")
    if env_session:
        return env_session

    # Try to find most recent session directory
    logs_dir = project_root / ".claude" / "runtime" / "logs"
    if logs_dir.exists():
        session_dirs = [
            d for d in logs_dir.iterdir()
            if d.is_dir() and len(d.name) == 15 and "_" in d.name
        ]
        if session_dirs:
            # Return most recent session
            latest = sorted(session_dirs, reverse=True)[0]
            return latest.name

    # Generate new session ID from current timestamp
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_conversation() -> None:
    """Save current conversation to transcript file.

    Reads conversation data from stdin (if provided by Claude Code)
    or attempts to capture current conversation state from available sources.
    """
    try:
        # Get current session ID
        session_id = get_current_session_id()
        session_dir = project_root / ".claude" / "runtime" / "logs" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Try to read conversation data from stdin
        conversation_data = []
        if not sys.stdin.isatty():
            try:
                input_text = sys.stdin.read().strip()
                if input_text:
                    input_data = json.loads(input_text)
                    # Extract conversation or messages
                    conversation_data = input_data.get("conversation", input_data.get("messages", []))
            except (json.JSONDecodeError, KeyError):
                pass

        # If no stdin data, create a manual save marker
        if not conversation_data:
            conversation_data = [{
                "role": "system",
                "content": f"Manual transcript save requested at {datetime.now().isoformat()}",
                "timestamp": datetime.now().isoformat()
            }]

        # Import ContextPreserver
        try:
            from context_preservation import ContextPreserver
        except ImportError:
            print("❌ Error: Could not import ContextPreserver")
            print("   Ensure context_preservation.py is available in .claude/tools/amplihack/")
            return

        # Create ContextPreserver instance
        preserver = ContextPreserver(session_id=session_id)
        preserver.session_dir = session_dir

        # Export conversation transcript
        transcript_path = preserver.export_conversation_transcript(conversation_data)

        # Display success message
        print("✅ Conversation transcript saved!")
        print("━" * 80)
        print(f"📄 Session ID: {session_id}")
        print(f"📂 Location: {transcript_path}")
        print(f"💬 Messages: {len(conversation_data)}")
        print()
        print("💡 Restore this session later with:")
        print(f"   /transcripts {session_id}")
        print()

        if len(conversation_data) == 1 and conversation_data[0].get("role") == "system":
            print("ℹ️  Note: No conversation data provided on stdin.")
            print("   A manual save marker was created.")
            print("   Full conversation transcripts are saved automatically")
            print("   by the PreCompact hook before context compaction.")

    except PermissionError as e:
        print(f"❌ Permission Error: Could not save transcript")
        print(f"   {str(e)}")
        print("   Check file permissions for .claude/runtime/logs/")
    except Exception as e:
        print(f"❌ Error saving conversation transcript: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for /transcripts command."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        # List available sessions
        sessions = list_available_sessions()
        display_session_list(sessions)

        if sessions:
            print("💡 Usage:")
            print("   /transcripts <session_id>  - Restore context from specific session")
            print("   /transcripts latest        - Restore context from most recent session")
            print("   /transcripts list          - Show this list again")
            print("   /transcripts save          - Save current conversation to transcript")

    elif args[0] == "list":
        # Explicit list command
        sessions = list_available_sessions()
        display_session_list(sessions)

    elif args[0] == "latest":
        # Restore latest session
        sessions = list_available_sessions()
        if sessions:
            restore_session_context(sessions[0])
        else:
            print("❌ No sessions found")

    elif args[0] == "save":
        # Save current conversation
        save_conversation()

    else:
        # Restore specific session
        session_id = args[0]
        restore_session_context(session_id)


if __name__ == "__main__":
    main()
