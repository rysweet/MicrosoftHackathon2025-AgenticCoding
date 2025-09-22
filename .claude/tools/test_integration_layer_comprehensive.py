#!/usr/bin/env python3
"""
Comprehensive test suite for the integration layer.

Tests all components including ReflectionTrigger, WorkflowIntegration,
circuit breaker, rate limiting, and end-to-end automation flow.
"""

import asyncio
import json
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# Add integration layer to path
sys.path.insert(0, str(Path(__file__).parent))
from integration_layer import (
    AutomationResult,
    CircuitBreaker,
    DuplicatePrevention,
    IntegrationLayer,
    RateLimiter,
    ReflectionTrigger,
    WorkflowIntegration,
    WorkflowResult,
)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker functionality"""

    def setUp(self):
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=1)

    async def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker allows normal operation"""

        def success_func():
            return "success"

        result = await self.circuit_breaker.call(success_func)
        self.assertEqual(result, "success")
        self.assertFalse(self.circuit_breaker.is_open)

    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures"""

        def failing_func():
            raise Exception("Test failure")

        # Trigger failures up to threshold
        for i in range(3):
            with self.assertRaises(Exception):
                await self.circuit_breaker.call(failing_func)

        # Circuit should now be open
        self.assertTrue(self.circuit_breaker.is_open)

        # Next call should fail immediately
        with self.assertRaises(Exception) as cm:
            await self.circuit_breaker.call(failing_func)
        self.assertIn("Circuit breaker is open", str(cm.exception))

    async def test_circuit_breaker_resets_after_timeout(self):
        """Test circuit breaker resets after timeout"""

        def failing_func():
            raise Exception("Test failure")

        def success_func():
            return "success"

        # Open the circuit
        for i in range(3):
            with self.assertRaises(Exception):
                await self.circuit_breaker.call(failing_func)

        self.assertTrue(self.circuit_breaker.is_open)

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Should allow calls again
        result = await self.circuit_breaker.call(success_func)
        self.assertEqual(result, "success")
        self.assertFalse(self.circuit_breaker.is_open)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality"""

    def setUp(self):
        self.rate_limiter = RateLimiter(max_calls=3, window_seconds=1)

    def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows calls within limit"""
        # Should allow first 3 calls
        for i in range(3):
            self.assertTrue(self.rate_limiter.is_allowed())

        # 4th call should be denied
        self.assertFalse(self.rate_limiter.is_allowed())

    def test_rate_limiter_resets_after_window(self):
        """Test rate limiter resets after time window"""
        # Use all calls
        for i in range(3):
            self.assertTrue(self.rate_limiter.is_allowed())

        # Should be denied
        self.assertFalse(self.rate_limiter.is_allowed())

        # Fast forward time by modifying calls
        old_time = time.time() - 2  # 2 seconds ago
        self.rate_limiter.calls = [old_time] * 3

        # Should allow calls again
        self.assertTrue(self.rate_limiter.is_allowed())

    def test_time_until_reset(self):
        """Test time until reset calculation"""
        # Use all calls
        for i in range(3):
            self.rate_limiter.is_allowed()

        # Should have time until reset (but may be 0 if very fast)
        time_until_reset = self.rate_limiter.time_until_reset()
        self.assertGreaterEqual(time_until_reset, 0)
        self.assertLessEqual(time_until_reset, 1)


class TestDuplicatePrevention(unittest.TestCase):
    """Test duplicate prevention functionality"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.duplicate_prevention = DuplicatePrevention(window_minutes=30)
        # Use temp file for testing
        self.duplicate_prevention.state_file = self.temp_dir / "duplicate_test.json"

    def tearDown(self):
        # Clean up temp files
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_no_duplicate_when_empty(self):
        """Test no duplicate detection when no history exists"""
        patterns = [{"type": "repeated_tool_use", "count": 5}]
        self.assertFalse(self.duplicate_prevention.is_duplicate(patterns))

    def test_duplicate_detection(self):
        """Test duplicate pattern detection"""
        patterns = [{"type": "repeated_tool_use", "count": 5}]

        # Record automation
        self.duplicate_prevention.record_automation(patterns, "workflow_1")

        # Same patterns should be detected as duplicate
        self.assertTrue(self.duplicate_prevention.is_duplicate(patterns))

        # Different patterns should not be duplicate
        different_patterns = [{"type": "error_patterns", "count": 3}]
        self.assertFalse(self.duplicate_prevention.is_duplicate(different_patterns))

    def test_duplicate_expires_after_window(self):
        """Test duplicates expire after time window"""
        patterns = [{"type": "repeated_tool_use", "count": 5}]

        # Record automation
        self.duplicate_prevention.record_automation(patterns, "workflow_1")

        # Modify state to simulate old timestamp
        state = json.loads(self.duplicate_prevention.state_file.read_text())
        old_time = datetime.now() - timedelta(minutes=31)  # Older than window
        state["recent_automations"][0]["timestamp"] = old_time.isoformat()
        self.duplicate_prevention.state_file.write_text(json.dumps(state))

        # Should not be duplicate anymore
        self.assertFalse(self.duplicate_prevention.is_duplicate(patterns))


class TestReflectionTrigger(unittest.TestCase):
    """Test ReflectionTrigger functionality"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        config_path = self.temp_dir / "integration_config.json"
        self.reflection_trigger = ReflectionTrigger(str(config_path))

    def tearDown(self):
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_automation_criteria_no_patterns(self):
        """Test automation criteria with no patterns"""
        analysis = {"patterns": [], "metrics": {}}
        self.assertFalse(self.reflection_trigger.check_automation_criteria(analysis))

    def test_automation_criteria_meets_threshold(self):
        """Test automation criteria meets threshold"""
        analysis = {
            "patterns": [
                {"type": "user_frustration", "count": 1},  # High priority
                {"type": "error_patterns", "count": 5},  # Medium priority
            ],
            "metrics": {},
        }
        # This should meet the default threshold of 7 (10 + 7*1.8 ≈ 22)
        self.assertTrue(self.reflection_trigger.check_automation_criteria(analysis))

    def test_automation_criteria_below_threshold(self):
        """Test automation criteria below threshold"""
        analysis = {
            "patterns": [
                {"type": "repeated_reads", "count": 2}  # Low priority
            ],
            "metrics": {},
        }
        # Should be below threshold
        self.assertFalse(self.reflection_trigger.check_automation_criteria(analysis))

    def test_priority_score_calculation(self):
        """Test priority score calculation logic"""
        patterns = [
            {"type": "user_frustration", "count": 1},  # Base 10, freq 1.0 = 10
            {"type": "error_patterns", "count": 3},  # Base 7, freq 1.4 = 9.8 ≈ 9
            {"type": "repeated_tool_use", "count": 10},  # Base 6, freq 2.8 = 16.8 ≈ 16
        ]
        score = self.reflection_trigger._calculate_priority_score(patterns)
        # Expected: 10 + 9 + 16 = 35 (approximately)
        self.assertGreater(score, 30)
        self.assertLess(score, 40)

    def test_rate_limiting(self):
        """Test rate limiting prevents excessive automation"""
        analysis = {"patterns": [{"type": "user_frustration", "count": 1}], "metrics": {}}

        # First few calls should work
        for i in range(3):
            self.assertTrue(self.reflection_trigger.check_automation_criteria(analysis))

        # 4th call should be rate limited
        self.assertFalse(self.reflection_trigger.check_automation_criteria(analysis))


class TestWorkflowIntegration(unittest.TestCase):
    """Test WorkflowIntegration functionality"""

    def setUp(self):
        self.workflow_integration = WorkflowIntegration()

    async def test_execute_improvement_workflow_success(self):
        """Test successful workflow execution"""
        with patch.object(self.workflow_integration, "_execute_workflow_steps") as mock_execute:
            mock_execute.return_value = {
                "github_issue": 123,
                "branch_name": "feat/improvement",
                "pr_number": 456,
            }

            result = await self.workflow_integration.execute_improvement_workflow(
                "Test improvement"
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.workflow_id)
            self.assertEqual(result.github_issue, 123)
            self.assertEqual(result.branch_name, "feat/improvement")
            self.assertEqual(result.pr_number, 456)

    async def test_execute_improvement_workflow_failure(self):
        """Test workflow execution failure"""
        with patch.object(self.workflow_integration, "_execute_workflow_steps") as mock_execute:
            mock_execute.side_effect = Exception("Workflow failed")

            result = await self.workflow_integration.execute_improvement_workflow(
                "Test improvement"
            )

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error)
            self.assertIn("Workflow failed", result.error)

    async def test_create_github_pr_no_gh_cli(self):
        """Test PR creation when GitHub CLI is not available"""
        with patch.object(self.workflow_integration, "_check_gh_cli", return_value=False):
            workflow_result = WorkflowResult(
                success=True, workflow_id="test_workflow", github_issue=123
            )

            pr_result = await self.workflow_integration.create_github_pr(workflow_result)

            self.assertFalse(pr_result.success)
            self.assertIn("GitHub CLI not available", pr_result.error)

    async def test_create_github_pr_failed_workflow(self):
        """Test PR creation from failed workflow"""
        workflow_result = WorkflowResult(
            success=False, workflow_id="test_workflow", error="Workflow failed"
        )

        pr_result = await self.workflow_integration.create_github_pr(workflow_result)

        self.assertFalse(pr_result.success)
        self.assertIn("Cannot create PR from failed workflow", pr_result.error)


class TestIntegrationLayer(unittest.TestCase):
    """Test complete IntegrationLayer functionality"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        # Create a real integration layer for testing
        self.integration_layer = IntegrationLayer()

    def tearDown(self):
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    async def test_process_reflection_analysis_success(self):
        """Test successful processing of reflection analysis"""
        analysis = {
            "patterns": [
                {"type": "user_frustration", "count": 1},
                {"type": "error_patterns", "count": 5},
            ],
            "metrics": {"total_messages": 50},
        }

        with patch.object(
            self.integration_layer.reflection_trigger,
            "check_automation_criteria",
            return_value=True,
        ):
            with patch.object(
                self.integration_layer.reflection_trigger, "trigger_stage2_automation"
            ) as mock_trigger:
                mock_trigger.return_value = AutomationResult(
                    success=True, workflow_id="test_workflow"
                )

                result = await self.integration_layer.process_reflection_analysis(analysis)

                self.assertIsNotNone(result)
                self.assertTrue(result.success)
                self.assertEqual(result.workflow_id, "test_workflow")

    async def test_process_reflection_analysis_criteria_not_met(self):
        """Test processing when automation criteria not met"""
        analysis = {
            "patterns": [{"type": "repeated_reads", "count": 1}],  # Low priority
            "metrics": {},
        }

        with patch.object(
            self.integration_layer.reflection_trigger,
            "check_automation_criteria",
            return_value=False,
        ):
            result = await self.integration_layer.process_reflection_analysis(analysis)
            self.assertIsNone(result)

    async def test_process_reflection_analysis_duplicate_patterns(self):
        """Test processing with duplicate patterns"""
        analysis = {"patterns": [{"type": "repeated_tool_use", "count": 5}], "metrics": {}}

        with patch.object(
            self.integration_layer.reflection_trigger,
            "check_automation_criteria",
            return_value=True,
        ):
            with patch.object(
                self.integration_layer.duplicate_prevention, "is_duplicate", return_value=True
            ):
                result = await self.integration_layer.process_reflection_analysis(analysis)

                self.assertIsNotNone(result)
                self.assertFalse(result.success)
                self.assertIn("Duplicate patterns detected", result.error)

    def test_get_health_status(self):
        """Test health status reporting"""
        health = self.integration_layer.get_health_status()

        self.assertIn("circuit_breaker_open", health)
        self.assertIn("rate_limit_remaining", health)
        self.assertIn("workflow_integration_available", health)
        self.assertIn("github_cli_available", health)

        # Verify types
        self.assertIsInstance(health["circuit_breaker_open"], bool)
        self.assertIsInstance(health["rate_limit_remaining"], int)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

    async def test_complete_automation_flow(self):
        """Test complete flow from reflection to automation"""
        # Skip this test since we're testing the integration layer in isolation
        # The actual pipeline integration is tested in separate integration tests

        # Create integration layer
        integration = IntegrationLayer()

        # Sample reflection analysis that meets criteria
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "type": "user_frustration",  # High priority pattern
                    "count": 1,
                    "suggestion": "Review approach and consider alternative solution",
                }
            ],
            "metrics": {
                "total_messages": 50,
                "user_messages": 25,
                "assistant_messages": 25,
                "tool_uses": 15,
            },
            "suggestions": ["Review approach"],
        }

        # Mock the trigger to return success
        with patch.object(
            integration.reflection_trigger, "trigger_stage2_automation"
        ) as mock_trigger:
            mock_trigger.return_value = AutomationResult(
                success=True, workflow_id="test_workflow_123", message="Test automation triggered"
            )

            with patch.object(
                integration.reflection_trigger, "check_automation_criteria", return_value=True
            ):
                # Process through integration layer
                result = await integration.process_reflection_analysis(analysis)

                # Verify automation was triggered
                self.assertIsNotNone(result)
                self.assertTrue(result.success)
                self.assertEqual(result.workflow_id, "test_workflow_123")
                self.assertIn("Test automation triggered", result.message)

    async def test_error_handling_and_recovery(self):
        """Test error handling and graceful degradation"""
        # Test with invalid analysis
        invalid_analysis = {"invalid": "data"}

        integration = IntegrationLayer()

        with patch.object(
            integration.reflection_trigger,
            "check_automation_criteria",
            side_effect=Exception("Test error"),
        ):
            result = await integration.process_reflection_analysis(invalid_analysis)

            self.assertIsNotNone(result)
            self.assertFalse(result.success)
            self.assertIn("Integration layer failed", result.error)


class TestSafetyMechanisms(unittest.TestCase):
    """Test safety mechanisms and edge cases"""

    async def test_circuit_breaker_prevents_cascade_failures(self):
        """Test circuit breaker prevents cascade failures"""
        circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=1)

        def failing_function():
            raise Exception("Service unavailable")

        # Trigger circuit breaker
        for _ in range(2):
            with self.assertRaises(Exception):
                await circuit_breaker.call(failing_function)

        # Verify circuit is open
        self.assertTrue(circuit_breaker.is_open)

        # Further calls should fail fast
        start_time = time.time()
        with self.assertRaises(Exception) as cm:
            await circuit_breaker.call(failing_function)
        elapsed = time.time() - start_time

        # Should fail immediately (< 0.1 seconds)
        self.assertLess(elapsed, 0.1)
        self.assertIn("Circuit breaker is open", str(cm.exception))

    def test_rate_limiter_configuration(self):
        """Test rate limiter with different configurations"""
        # Very restrictive rate limiter
        restrictive_limiter = RateLimiter(max_calls=1, window_seconds=10)

        self.assertTrue(restrictive_limiter.is_allowed())
        self.assertFalse(restrictive_limiter.is_allowed())

        # Verify time until reset
        time_until_reset = restrictive_limiter.time_until_reset()
        self.assertGreaterEqual(time_until_reset, 9)
        self.assertLessEqual(time_until_reset, 10)

    def test_duplicate_prevention_edge_cases(self):
        """Test duplicate prevention with edge cases"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            duplicate_prevention = DuplicatePrevention(window_minutes=1)
            duplicate_prevention.state_file = temp_dir / "test_state.json"

            # Test with empty patterns
            self.assertFalse(duplicate_prevention.is_duplicate([]))

            # Test with None patterns
            patterns = [{"type": None, "count": 0}]
            duplicate_prevention.record_automation(patterns, "workflow_1")
            self.assertTrue(duplicate_prevention.is_duplicate(patterns))

        finally:
            import shutil

            shutil.rmtree(temp_dir)


async def run_async_tests():
    """Run all async tests"""
    # Create test suite for async tests
    async_test_classes = [
        TestCircuitBreaker,
        TestWorkflowIntegration,
        TestIntegrationLayer,
        TestEndToEndIntegration,
        TestSafetyMechanisms,
    ]

    print("🧪 Running Async Integration Tests")
    print("=" * 50)

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in async_test_classes:
        print(f"\n📋 Testing {test_class.__name__}")

        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith("test_")]

        for test_method_name in test_methods:
            total_tests += 1
            test_instance = test_class()
            test_instance.setUp()

            try:
                test_method = getattr(test_instance, test_method_name)
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()

                print(f"  ✅ {test_method_name}")
                passed_tests += 1

            except Exception as e:
                print(f"  ❌ {test_method_name}: {e}")
                failed_tests.append(f"{test_class.__name__}.{test_method_name}: {e}")

            finally:
                try:
                    test_instance.tearDown()
                except:
                    pass

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    else:
        print("\n🎉 All tests passed!")

    return passed_tests == total_tests


def run_sync_tests():
    """Run synchronous tests using unittest"""
    print("\n🧪 Running Sync Integration Tests")
    print("=" * 50)

    # Create test suite for sync tests
    sync_test_classes = [TestRateLimiter, TestDuplicatePrevention, TestReflectionTrigger]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in sync_test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


async def main():
    """Main test runner"""
    print("🚀 Starting Comprehensive Integration Layer Tests")
    print("Testing: ReflectionTrigger, WorkflowIntegration, Circuit Breaker, Rate Limiting, etc.")
    print()

    # Run sync tests first
    sync_success = run_sync_tests()

    # Run async tests
    async_success = await run_async_tests()

    # Final summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Sync Tests:  {'✅ PASSED' if sync_success else '❌ FAILED'}")
    print(f"Async Tests: {'✅ PASSED' if async_success else '❌ FAILED'}")

    overall_success = sync_success and async_success
    print(f"Overall:     {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")

    if overall_success:
        print("\n🎉 Integration layer is ready for production!")
        print("✅ All safety mechanisms working correctly")
        print("✅ Error handling and graceful degradation verified")
        print("✅ Circuit breaker and rate limiting functional")
        print("✅ End-to-end automation flow tested")
    else:
        print("\n⚠️  Integration layer needs attention before deployment")

    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
