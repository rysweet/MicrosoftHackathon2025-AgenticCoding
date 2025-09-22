"""
Agent Invoker

Provides a mechanism to invoke agents from within Python code.
This bridges the gap between the WorkflowOrchestrator and actual agent execution.
"""

import asyncio
import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AgentInvocation:
    """Represents an agent invocation request"""

    agent_name: str
    task: str
    context: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300  # 5 minutes default


@dataclass
class AgentResult:
    """Result from agent execution"""

    success: bool
    agent_name: str
    output: str
    error: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class AgentInvoker:
    """
    Invokes agents by creating temporary task files and simulating their execution.

    In a production environment, this would integrate with the Task tool
    or directly with the Claude Code SDK to execute agents.
    """

    def __init__(self, agents_dir: Path = None, parallel_max: int = 4):
        """
        Initialize the agent invoker.

        Args:
            agents_dir: Directory containing agent definitions
            parallel_max: Maximum number of agents to run in parallel
        """
        self.agents_dir = agents_dir or Path(".claude/agents/amplihack")
        self.parallel_max = parallel_max
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=parallel_max)

    async def invoke_agent(self, invocation: AgentInvocation) -> AgentResult:
        """
        Invoke a single agent asynchronously.

        Args:
            invocation: Agent invocation request

        Returns:
            AgentResult with execution outcome
        """
        start_time = datetime.now()

        try:
            # Check if agent exists
            agent_path = self._find_agent_path(invocation.agent_name)
            if not agent_path:
                return AgentResult(
                    success=False,
                    agent_name=invocation.agent_name,
                    output="",
                    error=f"Agent '{invocation.agent_name}' not found",
                )

            # Create task context
            task_context = self._prepare_task_context(invocation)

            # Execute agent (simulation for now)
            output = await self._execute_agent_simulation(
                invocation.agent_name, invocation.task, task_context, invocation.timeout_seconds
            )

            duration = (datetime.now() - start_time).total_seconds()

            return AgentResult(
                success=True,
                agent_name=invocation.agent_name,
                output=output,
                duration_seconds=duration,
                metadata={"agent_path": str(agent_path)},
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return AgentResult(
                success=False,
                agent_name=invocation.agent_name,
                output="",
                error=str(e),
                duration_seconds=duration,
            )

    async def invoke_agents_parallel(self, invocations: List[AgentInvocation]) -> List[AgentResult]:
        """
        Invoke multiple agents in parallel.

        Args:
            invocations: List of agent invocation requests

        Returns:
            List of AgentResult objects
        """
        # Create tasks for parallel execution
        tasks = [self.invoke_agent(inv) for inv in invocations]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    AgentResult(
                        success=False,
                        agent_name=invocations[i].agent_name,
                        output="",
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def invoke_agent_sync(self, invocation: AgentInvocation) -> AgentResult:
        """Synchronous wrapper for agent invocation"""
        return asyncio.run(self.invoke_agent(invocation))

    def invoke_agents_parallel_sync(self, invocations: List[AgentInvocation]) -> List[AgentResult]:
        """Synchronous wrapper for parallel agent invocation"""
        return asyncio.run(self.invoke_agents_parallel(invocations))

    def _find_agent_path(self, agent_name: str) -> Optional[Path]:
        """
        Find the path to an agent definition file.

        Searches in multiple locations:
        1. Direct match in agents_dir
        2. In specialized/ subdirectory
        3. In workflows/ subdirectory
        4. With .md extension added
        """
        search_paths = [
            self.agents_dir / f"{agent_name}.md",
            self.agents_dir / f"{agent_name}",
            self.agents_dir / "specialized" / f"{agent_name}.md",
            self.agents_dir / "workflows" / f"{agent_name}.md",
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _prepare_task_context(self, invocation: AgentInvocation) -> Dict[str, Any]:
        """Prepare context for agent execution"""
        context = {
            "task": invocation.task,
            "timestamp": datetime.now().isoformat(),
            "agent": invocation.agent_name,
        }

        if invocation.context:
            context.update(invocation.context)

        return context

    async def _execute_agent_simulation(
        self, agent_name: str, task: str, context: Dict[str, Any], timeout: int
    ) -> str:
        """
        Simulate agent execution.

        In production, this would:
        1. Use the Task tool to invoke the agent
        2. Stream the agent's output
        3. Return the complete response

        For now, we simulate with predefined responses.
        """
        # Simulate async execution with a small delay
        await asyncio.sleep(0.1)

        # Generate simulated responses based on agent type
        agent_responses = {
            "prompt-writer": f"Clarified requirements:\n- Clear objective: {task}\n- Success criteria defined\n- Edge cases identified",
            "architect": "Architecture design:\n- Module structure: 3 components\n- Clear boundaries defined\n- Interfaces specified",
            "builder": "Implementation complete:\n- Code generated from specifications\n- All tests passing\n- No stubs or placeholders",
            "cleanup": "Refactoring complete:\n- Removed 30% of code\n- Simplified logic flow\n- Maintained functionality",
            "reviewer": "Review complete:\n- Philosophy compliance: PASS\n- Code quality: 8/10\n- No security issues found",
            "security": "Security scan:\n- No vulnerabilities detected\n- Best practices followed\n- Input validation present",
            "tester": "Tests created:\n- Unit tests: 15\n- Integration tests: 5\n- Coverage: 85%",
            "optimizer": "Optimization complete:\n- Performance improved by 25%\n- Memory usage reduced\n- No functionality changes",
            "patterns": "Pattern analysis:\n- Identified 3 reusable patterns\n- No anti-patterns detected\n- Consistency maintained",
            "analyzer": "Code analysis:\n- Complexity: Low\n- Dependencies: Minimal\n- Structure: Clear",
            "api-designer": "API design:\n- RESTful endpoints defined\n- Clear contracts specified\n- Versioning strategy included",
            "database": "Database design:\n- Schema optimized\n- Indexes defined\n- Migration path clear",
            "integration": "Integration complete:\n- External services connected\n- Error handling robust\n- Retry logic implemented",
            "ambiguity": "Ambiguity resolved:\n- Clarified 3 unclear requirements\n- Defined edge cases\n- Assumptions documented",
            "pre-commit-diagnostic": "Pre-commit checks:\n- All hooks passing\n- Code formatted\n- No linting errors",
            "ci-diagnostic-workflow": "CI status:\n- All checks green\n- Tests passing\n- Build successful",
        }

        # Get response for this agent or use default
        response = agent_responses.get(
            agent_name, f"Agent {agent_name} executed successfully for task: {task[:100]}..."
        )

        # Add context information
        if context.get("pattern_data"):
            pattern_type = context["pattern_data"].get("type", "unknown")
            response += f"\n\nPattern context: {pattern_type}"

        return response

    def get_available_agents(self) -> List[str]:
        """Get list of all available agents"""
        agents = []

        # Search for .md files in agents directory
        for agent_file in self.agents_dir.rglob("*.md"):
            if agent_file.is_file():
                agent_name = agent_file.stem
                agents.append(agent_name)

        return sorted(set(agents))

    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if an agent exists"""
        return self._find_agent_path(agent_name) is not None


# Convenience functions for direct usage


def invoke_agent(agent_name: str, task: str, context: Dict[str, Any] = None) -> AgentResult:
    """
    Quick function to invoke a single agent.

    Example:
        result = invoke_agent("architect", "Design authentication system")
        if result.success:
            print(result.output)
    """
    invoker = AgentInvoker()
    invocation = AgentInvocation(agent_name, task, context)
    return invoker.invoke_agent_sync(invocation)


def invoke_agents_parallel(invocations: List[Tuple[str, str]]) -> List[AgentResult]:
    """
    Quick function to invoke multiple agents in parallel.

    Example:
        invocations = [
            ("architect", "Design system"),
            ("security", "Review security"),
            ("tester", "Create test plan")
        ]
        results = invoke_agents_parallel(invocations)
    """
    invoker = AgentInvoker()
    agent_invocations = [AgentInvocation(agent, task) for agent, task in invocations]
    return invoker.invoke_agents_parallel_sync(agent_invocations)


if __name__ == "__main__":
    # Test the agent invoker
    print("Testing Agent Invoker\n")

    # Test single agent invocation
    print("1. Single agent invocation:")
    result = invoke_agent("architect", "Design a user authentication system")
    print(f"   Result: {result.success}")
    print(f"   Output: {result.output[:100]}...")
    print(f"   Duration: {result.duration_seconds:.2f}s\n")

    # Test parallel agent invocation
    print("2. Parallel agent invocation:")
    parallel_tasks = [
        ("prompt-writer", "Clarify requirements for API"),
        ("architect", "Design microservices architecture"),
        ("security", "Review authentication approach"),
        ("tester", "Create test strategy"),
    ]

    results = invoke_agents_parallel(parallel_tasks)
    for result in results:
        print(f"   - {result.agent_name}: {'SUCCESS' if result.success else 'FAILED'}")

    print("\n3. Available agents:")
    invoker = AgentInvoker()
    agents = invoker.get_available_agents()
    print(f"   Found {len(agents)} agents")
    for agent in agents[:5]:  # Show first 5
        print(f"   - {agent}")
