#!/usr/bin/env python3
"""
Unified Claude Code stop hook with configurable functionality.

Consolidates all stop hook implementations into a single, configurable version:
- Primary stop functionality with transcript bug fix
- Azure continuation logic (optional)
- Reflection automation (optional)
- Comprehensive transcript reading
- Local and UVX deployment compatibility

Configuration is handled via environment variables and runtime settings.
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import the base processor
sys.path.insert(0, str(Path(__file__).parent))
from hook_processor import HookProcessor


class UnifiedStopHook(HookProcessor):
    """Unified stop hook processor with configurable features."""

    def __init__(self):
        super().__init__("stop_unified")

        # Load configuration
        self.config = self._load_configuration()
        self.log(f"Unified stop hook initialized with config: {self.config}")

    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables and settings."""
        config = {
            # Core features
            "enable_reflection": True,  # Always enabled for learning
            "enable_automation": self._get_bool_env("CLAUDE_HOOK_ENABLE_AUTOMATION", True),
            "enable_azure_continuation": self._get_bool_env(
                "CLAUDE_HOOK_ENABLE_AZURE_CONTINUATION", True
            ),
            # Automation settings
            "automation_min_patterns": int(
                os.environ.get("CLAUDE_HOOK_AUTOMATION_MIN_PATTERNS", "2")
            ),
            "automation_timeout": int(os.environ.get("CLAUDE_HOOK_AUTOMATION_TIMEOUT", "30")),
            # Azure continuation settings
            "azure_continuation_timeout": int(os.environ.get("CLAUDE_HOOK_AZURE_TIMEOUT", "3600")),
            "azure_todo_check": self._get_bool_env("CLAUDE_HOOK_AZURE_TODO_CHECK", True),
            "azure_phrase_check": self._get_bool_env("CLAUDE_HOOK_AZURE_PHRASE_CHECK", True),
            # Transcript reading settings
            "transcript_read_timeout": int(os.environ.get("CLAUDE_HOOK_TRANSCRIPT_TIMEOUT", "10")),
            "transcript_max_size": int(os.environ.get("CLAUDE_HOOK_TRANSCRIPT_MAX_SIZE", "50"))
            * 1024
            * 1024,  # MB to bytes
        }

        # Check for runtime configuration file
        config_file = self.project_root / ".claude" / "runtime" / "stop_hook_config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    runtime_config = json.load(f)
                    config.update(runtime_config)
                    self.log(f"Loaded runtime config from {config_file}")
            except Exception as e:
                self.log(f"Error loading runtime config: {e}", "WARNING")

        return config

    def _get_bool_env(self, env_var: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.environ.get(env_var, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    # ============================================================================
    # CORE TRANSCRIPT READING (with bug fix)
    # ============================================================================

    def read_transcript(self, transcript_path: str) -> List[Dict]:
        """Read and parse transcript file.

        INCLUDES CRITICAL BUG FIX: Handles transcript_path: None properly.

        Args:
            transcript_path: Path to transcript file

        Returns:
            List of messages from transcript
        """
        try:
            if not transcript_path:
                self.log("No transcript path provided", "WARNING")
                return []

            transcript_file = Path(transcript_path)
            if not transcript_file.exists():
                self.log(f"Transcript file not found: {transcript_path}", "WARNING")
                return []

            # Allow reading from Claude Code directories and temp directories
            # These are trusted locations where Claude Code stores transcripts
            allowed_external_paths = [
                Path.home() / ".claude",  # Claude Code's data directory
                Path("/tmp"),  # Temporary files
                Path("/var/folders"),  # macOS temp directory
                Path("/private/var/folders"),  # macOS temp directory (resolved)
            ]

            # Check if the transcript is in an allowed external location
            is_allowed_external = False
            for allowed_path in allowed_external_paths:
                try:
                    transcript_file.resolve().relative_to(allowed_path.resolve())
                    is_allowed_external = True
                    break
                except (ValueError, RuntimeError):
                    continue

            # If not in allowed external location, validate it's within project
            if not is_allowed_external:
                try:
                    self.validate_path_containment(transcript_file)
                except ValueError as e:
                    self.log(f"Transcript path not in allowed locations: {e}", "WARNING")
                    # Don't completely fail - just log the issue
                    pass

            self.log(f"Reading transcript from: {transcript_path}")

            with open(transcript_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                self.log("Transcript file is empty", "WARNING")
                return []

            # Try parsing as JSON first
            try:
                data = json.loads(content)

                # Handle different transcript formats
                if isinstance(data, list):
                    # Direct list of messages
                    self.log(f"Parsed JSON array with {len(data)} items")
                    return data
                elif isinstance(data, dict):
                    # Wrapped format
                    if "messages" in data:
                        messages = data["messages"]
                        self.log(f"Found 'messages' key with {len(messages)} messages")
                        return messages
                    elif "conversation" in data:
                        conversation = data["conversation"]
                        self.log(f"Found 'conversation' key with {len(conversation)} messages")
                        return conversation
                    else:
                        self.log(f"Unexpected transcript format: {list(data.keys())}", "WARNING")
                        return []
                else:
                    self.log(f"Unexpected transcript data type: {type(data)}", "WARNING")
                    return []

            except json.JSONDecodeError:
                # Try parsing as JSONL (one JSON object per line) - Claude Code's format
                self.log("Parsing as JSONL format (Claude Code transcript)")
                messages = []
                for line_num, line in enumerate(content.split("\n"), 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)

                        # Claude Code JSONL format has nested message structure
                        if isinstance(entry, dict):
                            # Extract the actual message from Claude Code format
                            if "message" in entry and isinstance(entry["message"], dict):
                                # This is Claude Code format - extract the nested message
                                message = entry["message"]
                                if "role" in message:
                                    messages.append(message)
                            elif "role" in entry:
                                # Direct message format
                                messages.append(entry)
                            elif "type" in entry:
                                # Some entries are metadata - skip them
                                if entry["type"] in ["user", "assistant"]:
                                    # Try to extract message if it exists
                                    if "message" in entry:
                                        messages.append(entry["message"])
                                else:
                                    self.log(
                                        f"Skipping metadata entry with type: {entry.get('type')}",
                                        "DEBUG",
                                    )
                    except json.JSONDecodeError as e:
                        # Log but continue - some lines might be metadata
                        self.log(f"Skipping non-JSON line {line_num}: {str(e)[:100]}", "DEBUG")
                        continue

                self.log(f"Parsed JSONL with {len(messages)} messages")
                return messages

        except Exception as e:
            self.log(f"Error reading transcript: {e}", "ERROR")
            return []

    def get_session_messages(self, input_data: Dict[str, Any]) -> List[Dict]:
        """Get session messages using multiple strategies.

        INCLUDES CRITICAL BUG FIX: Handles transcript_path: None properly.

        Args:
            input_data: Input from Claude Code

        Returns:
            List of session messages
        """
        # Strategy 1: Direct messages (highest priority - most reliable)
        if "messages" in input_data:
            messages = input_data["messages"]
            if messages:
                self.log(f"Using direct messages: {len(messages)} messages")
                return messages

        # Strategy 2: Provided transcript path
        transcript_path = input_data.get("transcript_path")

        # CRITICAL BUG FIX: Handle different types of transcript_path values
        if transcript_path:
            # Convert to string if it's not already
            if not isinstance(transcript_path, str):
                self.log(f"transcript_path is type {type(transcript_path)}, converting to string")
                # Handle None or other non-string types
                if transcript_path is None or str(transcript_path) in ["None", "null", ""]:
                    transcript_path = None
                else:
                    transcript_path = str(transcript_path)

            if transcript_path and transcript_path.strip() and transcript_path != "None":
                messages = self.read_transcript(transcript_path)
                if messages:
                    self.log(
                        f"Read {len(messages)} messages from provided transcript: {transcript_path}"
                    )
                    return messages
                else:
                    self.log(f"No messages found at provided transcript path: {transcript_path}")

        # Strategy 3: Find transcript using session_id
        session_id = input_data.get("session_id")
        if session_id:
            transcript_file = self.find_session_transcript(session_id)
            if transcript_file:
                messages = self.read_transcript(str(transcript_file))
                if messages:
                    self.log(
                        f"Read {len(messages)} messages from discovered transcript: {transcript_file}"
                    )
                    return messages

        # Strategy 4: Search for recent transcript files in common locations
        self.log("Searching for recent transcript files...")
        transcript_locations = [
            self.project_root / ".claude" / "runtime" / "transcripts",
            self.project_root / ".claude" / "runtime" / "sessions",
            self.project_root / "transcripts",
        ]

        for location in transcript_locations:
            if not location.exists():
                continue

            # Find most recent transcript file
            try:
                transcript_files = list(location.glob("*.json"))
                if transcript_files:
                    # Sort by modification time, most recent first
                    transcript_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                    recent_file = transcript_files[0]

                    # Only use if it's very recent (within last hour)
                    import time

                    if time.time() - recent_file.stat().st_mtime < 3600:
                        messages = self.read_transcript(str(recent_file))
                        if messages:
                            self.log(
                                f"Using recent transcript: {recent_file} ({len(messages)} messages)"
                            )
                            return messages
            except Exception as e:
                self.log(f"Error searching in {location}: {e}", "WARNING")

        # No messages found
        self.log("No session messages found using any strategy", "WARNING")
        return []

    def find_session_transcript(self, session_id: str) -> Optional[Path]:
        """Find transcript file for a given session ID."""
        if not session_id:
            return None

        # Possible transcript locations and naming patterns
        possible_locations = [
            # Current runtime structure
            self.project_root / ".claude" / "runtime" / "transcripts",
            self.project_root / ".claude" / "runtime" / "sessions",
            self.project_root / ".claude" / "runtime" / "logs" / session_id,
            # Alternative naming patterns
            self.project_root / "transcripts",
            self.project_root / "sessions",
            # Temporary locations
            Path("/tmp") / "claude" / "transcripts",
        ]

        # Possible file patterns
        patterns = [
            f"{session_id}.json",
            f"{session_id}_transcript.json",
            f"transcript_{session_id}.json",
            f"session_{session_id}.json",
            "transcript.json",
            "messages.json",
            "conversation.json",
        ]

        for location in possible_locations:
            if not location.exists():
                continue

            for pattern in patterns:
                transcript_file = location / pattern
                if transcript_file.exists():
                    self.log(f"Found transcript file: {transcript_file}")
                    return transcript_file

        return None

    # ============================================================================
    # REFLECTION AND LEARNING EXTRACTION
    # ============================================================================

    def extract_learnings(self, messages: List[Dict]) -> Tuple[List[Dict], Optional[Dict]]:
        """Extract learnings using the reflection module.

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (learnings list, analysis dict)
        """
        if not self.config["enable_reflection"]:
            self.log("Reflection disabled by configuration")
            return [], None

        try:
            # Import reflection module
            from reflection import SessionReflector, save_reflection_summary

            # Create reflector and analyze session
            reflector = SessionReflector()
            analysis = reflector.analyze_session(messages)

            # Save detailed analysis if not skipped
            if not analysis.get("skipped"):
                summary_file = save_reflection_summary(analysis, self.analysis_dir)
                if summary_file:
                    self.log(f"Reflection analysis saved to {summary_file}")

                # Return patterns found as learnings
                learnings = []
                for pattern in analysis.get("patterns", []):
                    learnings.append(
                        {
                            "type": pattern["type"],
                            "suggestion": pattern.get("suggestion", ""),
                            "priority": "high"
                            if pattern["type"] == "user_frustration"
                            else "normal",
                            "count": pattern.get("count", 1),
                            "context": pattern.get("context", {}),
                        }
                    )
                return learnings, analysis
            else:
                self.log("Reflection skipped (loop prevention active)")
                return [], None

        except ImportError as e:
            self.log(f"Could not import reflection module: {e}", "WARNING")
            # Fall back to simple keyword extraction
            return self.extract_learnings_simple(messages), None
        except Exception as e:
            self.log(f"Error in reflection analysis: {e}", "ERROR")
            return [], None

    def extract_learnings_simple(self, messages: List[Dict]) -> List[Dict]:
        """Simple fallback learning extraction."""
        learnings = []
        keywords = ["discovered", "learned", "found that", "issue was", "solution was"]

        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        learnings.append({"keyword": keyword, "preview": content[:200]})
                        break
        return learnings

    # ============================================================================
    # AZURE CONTINUATION LOGIC
    # ============================================================================

    def is_proxy_active(self) -> bool:
        """Check if Azure OpenAI proxy is active."""
        if not self.config["enable_azure_continuation"]:
            return False

        try:
            # Check for proxy environment variables
            base_url = os.environ.get("ANTHROPIC_BASE_URL", "")

            # Proxy is active if ANTHROPIC_BASE_URL is set to localhost
            if "localhost" in base_url or "127.0.0.1" in base_url:
                self.log(f"Proxy detected via ANTHROPIC_BASE_URL: {base_url}")
                return True

            # Check for other proxy indicators
            if os.environ.get("CLAUDE_CODE_PROXY_LAUNCHER"):
                self.log("Proxy detected via CLAUDE_CODE_PROXY_LAUNCHER")
                return True

            if os.environ.get("AZURE_OPENAI_KEY"):
                self.log("Proxy detected via AZURE_OPENAI_KEY")
                return True

            # Check if we're running with Azure config
            if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_BASE_URL"):
                openai_url = os.environ.get("OPENAI_BASE_URL", "")
                if "azure" in openai_url.lower() or "openai.azure.com" in openai_url:
                    self.log(f"Azure detected via OPENAI_BASE_URL: {openai_url}")
                    return True

            return False
        except Exception as e:
            self.log(f"Error checking proxy status: {e}", "ERROR")
            return False

    def extract_todo_items(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract TODO items from messages that used TodoWrite tool."""
        if not self.config["azure_todo_check"]:
            return []

        todos = []
        try:
            for message in messages:
                if message.get("role") == "assistant":
                    content = message.get("content", "")

                    # Look for TodoWrite tool use
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                if item.get("name") == "TodoWrite":
                                    input_data = item.get("input", {})
                                    if "todos" in input_data:
                                        todos = input_data["todos"]
                                        self.log(f"Found {len(todos)} TODO items")
        except Exception as e:
            self.log(f"Error extracting TODO items: {e}", "ERROR")

        return todos

    def has_uncompleted_todos(self, todos: List[Dict[str, Any]]) -> bool:
        """Check if there are uncompleted TODO items."""
        for todo in todos:
            status = todo.get("status", "").lower()
            if status in ["pending", "in_progress"]:
                self.log(f"Found uncompleted todo: {todo.get('content', 'Unknown')}")
                return True
        return False

    def check_for_continuation_phrases(self, messages: List[Dict[str, Any]]) -> bool:
        """Check if assistant mentioned next steps or continuation."""
        if not self.config["azure_phrase_check"]:
            return False

        continuation_phrases = [
            r"next[ ,]+(?:i'll|let me|we'll|step)",
            r"(?:will|going to|about to|now i'll)[ ]+(?:create|implement|add|fix|update|work)",
            r"let me (?:now |also |next )?(?:create|implement|add|fix|update|work)",
            r"now let me",
            r"continuing with",
            r"moving on to",
            r"now for the",
            r"(?:after|once) (?:this|that),? (?:i'll|we'll|let's)",
            r"then (?:i'll|we'll|let me)",
            r"(?:first|second|third|next|finally),? (?:i'll|let me|we'll)",
            r"todo(?:s)? (?:list|items?)",
            r"remaining (?:tasks?|items?|work)",
            r"still need to",
        ]

        try:
            # Check last few assistant messages
            assistant_messages = [msg for msg in messages[-5:] if msg.get("role") == "assistant"]

            for message in assistant_messages:
                content = message.get("content", "")
                if isinstance(content, str):
                    content_lower = content.lower()
                    for pattern in continuation_phrases:
                        if re.search(pattern, content_lower):
                            self.log(f"Found continuation phrase matching: {pattern}")
                            return True
                elif isinstance(content, list):
                    # Check text content in structured messages
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "").lower()
                            for pattern in continuation_phrases:
                                if re.search(pattern, text):
                                    self.log(f"Found continuation phrase matching: {pattern}")
                                    return True
        except Exception as e:
            self.log(f"Error checking continuation phrases: {e}", "ERROR")

        return False

    def should_continue_azure(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Determine if Azure continuation should occur."""
        if not self.is_proxy_active():
            return None

        try:
            # Extract TODO items
            todos = self.extract_todo_items(messages)

            # Check condition 1: Uncompleted TODO items
            if self.has_uncompleted_todos(todos):
                self.log("Azure continuation: Continue - uncompleted TODOs found")
                return {
                    "decision": "continue",
                    "reason": "azure_uncompleted_todos",
                    "instructions": "Continue working on remaining tasks. Check TODO list and complete any pending items.",
                }

            # Check condition 2: Continuation phrases
            if self.check_for_continuation_phrases(messages):
                self.log("Azure continuation: Continue - continuation phrases found")
                return {
                    "decision": "continue",
                    "reason": "azure_continuation_phrases",
                    "instructions": "Continue working on the tasks you mentioned in your last messages.",
                }

            self.log("Azure continuation: Allow stop - no continuation indicators found")
            return None

        except Exception as e:
            self.log(f"Error in Azure continuation logic: {e}", "ERROR")
            return None

    # ============================================================================
    # AUTOMATION INTEGRATION
    # ============================================================================

    async def trigger_automation_if_needed(self, analysis: Dict) -> Optional[Dict[str, Any]]:
        """Trigger automation if analysis meets criteria."""
        if not self.config["enable_automation"]:
            self.log("Automation disabled by configuration")
            return None

        if not analysis or analysis.get("skipped"):
            self.log("No analysis available for automation")
            return None

        try:
            # Import automation components
            try:
                from integration_layer import IntegrationLayer

                integration_layer = IntegrationLayer()
                INTEGRATION_AVAILABLE = True
            except ImportError:
                self.log("Integration layer not available - trying reflection pipeline")
                try:
                    from reflection_automation_pipeline import (
                        ReflectionAutomationPipeline,
                        convert_reflection_analysis_to_result,
                    )

                    INTEGRATION_AVAILABLE = False
                except ImportError:
                    self.log("No automation components available")
                    return None

            self.log("Checking automation criteria...")

            if INTEGRATION_AVAILABLE:
                # Use integration layer
                automation_result = await integration_layer.process_reflection_analysis(analysis)
                if automation_result and automation_result.success:
                    self.log(
                        f"✅ Automation triggered via integration layer: {automation_result.workflow_id}"
                    )
                    return {
                        "decision": "continue",
                        "reason": "automation_triggered_integration",
                        "workflow_id": automation_result.workflow_id,
                        "instructions": f"""🤖 Automation Triggered Successfully!

**Workflow ID**: {automation_result.workflow_id}

{automation_result.message}

The automation system will:
1. Create a GitHub issue for the detected patterns
2. Design a solution following the 13-step workflow
3. Implement improvements with proper validation
4. Create a PR for review

Check `.claude/runtime/improvement_queue/` for progress updates.""",
                    }
            else:
                # Use reflection pipeline directly
                reflection_result = convert_reflection_analysis_to_result(analysis)
                if reflection_result and reflection_result.is_automation_worthy():
                    pipeline = ReflectionAutomationPipeline()
                    workflow_id = await pipeline.process_reflection_result(reflection_result)

                    if workflow_id:
                        self.log(f"✅ Automation triggered via pipeline: {workflow_id}")
                        primary_pattern = reflection_result.get_primary_issue()
                        pattern_desc = (
                            f"{primary_pattern.type} (severity: {primary_pattern.severity})"
                            if primary_pattern
                            else "unknown pattern"
                        )

                        return {
                            "decision": "continue",
                            "reason": "automation_triggered_pipeline",
                            "workflow_id": workflow_id,
                            "instructions": f"""🤖 Automation Triggered for Pattern Detection!

**Pattern**: {pattern_desc}
**Workflow ID**: {workflow_id}

Analyzing detected patterns and creating improvement plan. The automation will:
1. Create GitHub issue for improvement opportunity
2. Design solution following 13-step workflow
3. Implement improvement with validation
4. Create PR for review

Check `.claude/runtime/improvement_queue/` for progress.""",
                        }

            self.log("No automation triggered - criteria not met")
            return None

        except Exception as e:
            self.log(f"Error in automation trigger: {e}", "ERROR")
            return None

    # ============================================================================
    # MAIN PROCESSING LOGIC
    # ============================================================================

    def save_session_analysis(self, messages: List[Dict]):
        """Save session analysis for later review."""
        # Generate analysis filename
        analysis_file = (
            self.analysis_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Extract stats
        stats = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "tool_uses": 0,
            "errors": 0,
        }

        # Count tool uses and errors
        for msg in messages:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if "tool_use" in str(content):
                    stats["tool_uses"] += 1
                if "error" in str(content).lower():
                    stats["errors"] += 1

        # Extract learnings
        learnings, _ = self.extract_learnings(messages)
        if learnings:
            stats["potential_learnings"] = len(learnings)

        # Save analysis
        analysis = {"stats": stats, "learnings": learnings, "config": self.config}

        try:
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2)

            self.log(f"Saved session analysis to {analysis_file.name}")

            # Also save metrics
            self.save_metric("message_count", stats["message_count"])
            self.save_metric("tool_uses", stats["tool_uses"])
            self.save_metric("errors", stats["errors"])
            if learnings:
                self.save_metric("potential_learnings", len(learnings))
        except Exception as e:
            self.log(f"Error saving session analysis: {e}", "ERROR")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method for unified stop hook."""
        # Debug log the input data
        self.log(f"Unified stop hook processing - input keys: {list(input_data.keys())}")

        # Log configuration status
        enabled_features = [k for k, v in self.config.items() if k.startswith("enable_") and v]
        self.log(f"Enabled features: {enabled_features}")

        # Extract messages using robust method with bug fix
        messages = self.get_session_messages(input_data)
        self.log(f"Processing {len(messages)} messages")

        if not messages:
            self.log("No messages found - returning empty response")
            return {}

        # Save session analysis
        self.save_session_analysis(messages)

        # Extract learnings and analysis
        learnings, analysis = self.extract_learnings(messages)

        # Check Azure continuation first (higher priority)
        azure_result = self.should_continue_azure(messages)
        if azure_result:
            self.log(f"Azure continuation triggered: {azure_result['reason']}")
            return azure_result

        # Check automation opportunities
        automation_result = None
        if analysis and self.config["enable_automation"]:
            try:
                # Run automation in async context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    automation_result = loop.run_until_complete(
                        self.trigger_automation_if_needed(analysis)
                    )
                finally:
                    loop.close()
            except Exception as e:
                self.log(f"Error running automation check: {e}", "ERROR")

        if automation_result:
            self.log(f"Automation triggered: {automation_result['workflow_id']}")
            return automation_result

        # Build standard response with learnings
        output = self._build_learnings_response(learnings)

        self.log(f"Unified stop hook completed - returning {len(output)} metadata fields")
        return output

    def _build_learnings_response(self, learnings: List[Dict]) -> Dict[str, Any]:
        """Build response with learning information."""
        if not learnings:
            return {}

        # Check for high priority learnings
        priority_learnings = [
            learning for learning in learnings if learning.get("priority") == "high"
        ]

        output = {
            "metadata": {
                "learningsFound": len(learnings),
                "highPriority": len(priority_learnings),
                "source": "unified_stop_hook",
                "analysisPath": ".claude/runtime/analysis/",
                "summary": f"Found {len(learnings)} improvement opportunities",
                "configuredFeatures": [
                    k for k, v in self.config.items() if k.startswith("enable_") and v
                ],
            }
        }

        # Add specific suggestions to output if high priority
        if priority_learnings:
            output["metadata"]["urgentSuggestion"] = priority_learnings[0].get("suggestion", "")

        self.log(
            f"Found {len(learnings)} potential improvements "
            f"({len(priority_learnings)} high priority)"
        )

        return output


def main():
    """Entry point for the unified stop hook."""
    hook = UnifiedStopHook()
    hook.run()


if __name__ == "__main__":
    main()
