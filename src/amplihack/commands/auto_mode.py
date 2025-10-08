"""
Auto-Mode Slash Command Implementation

Provides the /amplihack:auto-mode command for persistent analysis and  # noqa
autonomous progression through objectives using Claude Agent SDK.

# noqa: print - CLI/slash command code uses print for output
# noqa - "amplihack" is the project name, not a development artifact
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from amplihack.sdk import AutoModeConfig, AutoModeOrchestrator, StateIntegrationError  # noqa


class AutoModeCommand:
    """Implementation of the /amplihack:auto-mode slash command"""  # noqa

    def __init__(self):
        self.orchestrator: Optional[AutoModeOrchestrator] = None
        self.active_session_id: Optional[str] = None

    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute auto-mode command with given arguments.

        Args:
            args: Command line arguments

        Returns:
            Command execution result
        """
        if not args:
            return self._show_help()

        command = args[0].lower()

        try:
            if command == "start":
                return await self._start_command(args[1:])
            if command == "process":
                return await self._process_command(args[1:])
            if command == "status":
                return await self._status_command(args[1:])
            if command == "pause":
                return await self._pause_command(args[1:])
            if command == "resume":
                return await self._resume_command(args[1:])
            if command == "stop":
                return await self._stop_command(args[1:])
            if command == "help":
                return self._show_help()
            return {
                "success": False,
                "error": f"Unknown command: {command}",
                "help": "Use '/amplihack:auto-mode help' for usage information",  # noqa
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {e!s}",
                "type": type(e).__name__,
            }

    async def _start_command(self, args: List[str]) -> Dict[str, Any]:
        """Start a new auto-mode session"""
        if not args:
            return {
                "success": False,
                "error": "Objective is required",
                "usage": '/amplihack:auto-mode start "Objective description"',  # noqa
            }

        # Parse arguments
        objective = args[0]
        working_dir = os.getcwd()
        max_iterations = 50

        # Parse optional arguments
        i = 1
        while i < len(args):
            if args[i] == "--working-dir" and i + 1 < len(args):
                working_dir = args[i + 1]
                i += 2
            elif args[i] == "--max-iterations" and i + 1 < len(args):
                max_iterations = int(args[i + 1])
                i += 2
            else:
                i += 1

        try:
            # Create orchestrator if not exists
            if not self.orchestrator:
                config = AutoModeConfig(
                    max_iterations=max_iterations,
                    persistence_enabled=True,
                    auto_progression_enabled=True,
                )
                self.orchestrator = AutoModeOrchestrator(config)

            # Start session
            session_id = await self.orchestrator.start_auto_mode_session(objective, working_dir)
            self.active_session_id = session_id

            return {
                "success": True,
                "session_id": session_id,
                "objective": objective,
                "working_directory": working_dir,
                "max_iterations": max_iterations,
                "state": "active",
                "message": f"Auto-mode session started for: {objective[:60]}...",
            }

        except StateIntegrationError as e:
            return {
                "success": False,
                "error": f"Failed to start session: {e!s}",
                "type": "StateIntegrationError",
            }

    async def _process_command(self, args: List[str]) -> Dict[str, Any]:
        """Process Claude Code output through auto-mode analysis"""
        if not args:
            return {
                "success": False,
                "error": "Claude output is required",
                "usage": '/amplihack:auto-mode process "Claude output text"',  # noqa
            }

        if not self.orchestrator or not self.active_session_id:
            return {
                "success": False,
                "error": "No active auto-mode session. Start one with 'auto-mode start'",
                "suggestion": "Use '/amplihack:auto-mode start \"Your objective\"' first",  # noqa
            }

        claude_output = args[0]

        # Parse optional session ID (currently not used)
        i = 1
        while i < len(args):
            if args[i] == "--session-id" and i + 1 < len(args):
                # Skip session-id argument for now (not used in current implementation)
                i += 2
            else:
                i += 1

        try:
            # Process output
            result = await self.orchestrator.process_claude_output(
                claude_output, {"processed_at": datetime.now().isoformat()}
            )

            # Format response
            response = {
                "success": True,
                "session_id": self.active_session_id,
                "iteration": result["iteration"],
                "analysis": {
                    "confidence": result["confidence"],
                    "findings": result["analysis"]["findings"][:3],  # Top 3 findings
                    "quality_score": result["analysis"]["quality_score"],
                    "ai_reasoning": result["analysis"]["ai_reasoning"][:200]
                    + "...",  # Truncate for display
                },
                "recommendations": result["analysis"]["recommendations"][
                    :3
                ],  # Top 3 recommendations
                "should_continue": result["should_continue"],
                "state": result["state"],
            }

            # Add next action if available
            if result.get("next_action"):
                response["next_prompt"] = result["next_action"]
                response["message"] = "Analysis complete. Next prompt generated."
            else:
                response["message"] = "Analysis complete. Manual intervention may be needed."

            return response

        except StateIntegrationError as e:
            return {
                "success": False,
                "error": f"Processing failed: {e!s}",
                "type": "StateIntegrationError",
            }

    async def _status_command(self, args: List[str]) -> Dict[str, Any]:
        """Get current auto-mode session status"""
        if not self.orchestrator:
            return {
                "success": False,
                "error": "No auto-mode session active",
                "suggestion": "Start a session with '/amplihack:auto-mode start'",  # noqa
            }

        try:
            current_state = self.orchestrator.get_current_state()
            progress_summary = self.orchestrator.get_progress_summary()

            # Get session stats
            session_stats = self.orchestrator.session_manager.get_session_stats()
            analysis_stats = self.orchestrator.analysis_engine.get_analysis_stats()

            return {
                "success": True,
                "session": {
                    "id": current_state["session_id"],
                    "state": current_state["state"],
                    "iteration": current_state["iteration"],
                    "error_count": current_state["error_count"],
                },
                "progress": {
                    "milestones": progress_summary["milestones"],
                    "progress_percentage": progress_summary["progress_percentage"],
                    "average_confidence": progress_summary.get("average_confidence", 0.0),
                },
                "statistics": {
                    "total_sessions": session_stats["total_sessions"],
                    "active_sessions": session_stats["active_sessions"],
                    "total_analyses": analysis_stats["total_analyses"],
                    "cache_hit_rate": analysis_stats.get("cache_hit_rate", 0.0),
                },
                "context": {
                    "objective": self.orchestrator.current_context.user_objective
                    if self.orchestrator.current_context
                    else "Unknown",
                    "working_directory": self.orchestrator.current_context.working_directory
                    if self.orchestrator.current_context
                    else "Unknown",
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Status check failed: {e!s}",
                "type": type(e).__name__,
            }

    async def _pause_command(self, args: List[str]) -> Dict[str, Any]:
        """Pause auto-mode session"""
        if not self.orchestrator:
            return {"success": False, "error": "No auto-mode session to pause"}

        try:
            await self.orchestrator.pause_auto_mode()
            return {"success": True, "message": "Auto-mode session paused", "state": "paused"}

        except Exception as e:
            return {"success": False, "error": f"Failed to pause: {e!s}"}

    async def _resume_command(self, args: List[str]) -> Dict[str, Any]:
        """Resume auto-mode session"""
        if not self.orchestrator:
            return {"success": False, "error": "No auto-mode session to resume"}

        try:
            await self.orchestrator.resume_auto_mode()
            return {"success": True, "message": "Auto-mode session resumed", "state": "active"}

        except Exception as e:
            return {"success": False, "error": f"Failed to resume: {e!s}"}

    async def _stop_command(self, args: List[str]) -> Dict[str, Any]:
        """Stop auto-mode session"""
        if not self.orchestrator:
            return {"success": False, "error": "No auto-mode session to stop"}

        try:
            # Get final stats before stopping
            current_state = self.orchestrator.get_current_state()
            progress_summary = self.orchestrator.get_progress_summary()

            await self.orchestrator.stop_auto_mode()

            # Clean up
            self.orchestrator = None
            self.active_session_id = None

            return {
                "success": True,
                "message": "Auto-mode session stopped",
                "final_stats": {
                    "total_iterations": current_state["iteration"],
                    "milestones_achieved": progress_summary["milestones"],
                    "final_progress": progress_summary["progress_percentage"],
                },
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to stop: {e!s}"}

    def _show_help(self) -> Dict[str, Any]:
        """Show help information for auto-mode command"""
        return {
            "success": True,
            "command": "/amplihack:auto-mode",  # noqa
            "description": "Persistent analysis and autonomous progression through objectives",
            "usage": {
                "start": {
                    "syntax": '/amplihack:auto-mode start "Objective" [--working-dir /path] [--max-iterations 50]',  # noqa
                    "description": "Start new auto-mode session",
                    "example": '/amplihack:auto-mode start "Build a REST API with authentication"',  # noqa
                },
                "process": {
                    "syntax": '/amplihack:auto-mode process "Claude output"',  # noqa
                    "description": "Process Claude Code output through analysis",
                    "example": '/amplihack:auto-mode process "I\'ve implemented the user authentication system."',  # noqa
                },
                "status": {
                    "syntax": "/amplihack:auto-mode status",  # noqa
                    "description": "Check current session status and progress",
                },
                "pause": {
                    "syntax": "/amplihack:auto-mode pause",  # noqa
                    "description": "Pause the current session",
                },
                "resume": {
                    "syntax": "/amplihack:auto-mode resume",  # noqa
                    "description": "Resume a paused session",
                },
                "stop": {
                    "syntax": "/amplihack:auto-mode stop",  # noqa
                    "description": "Stop and cleanup current session",
                },
            },
            "features": [
                "Real-time progress analysis using Claude Agent SDK",
                "Automatic next prompt generation",
                "Session persistence and recovery",
                "Quality assessment and recommendations",
                "Milestone tracking and progress monitoring",
                "Error handling and recovery mechanisms",
            ],
        }


# Command line interface for testing
async def main():
    """Test interface for auto-mode command"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python auto_mode.py <command> [args...]")  # noqa: T201 (print)
        return

    command = AutoModeCommand()
    result = await command.execute(sys.argv[1:])

    print(json.dumps(result, indent=2))  # noqa: T201 (print)


if __name__ == "__main__":
    asyncio.run(main())
