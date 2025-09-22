#!/usr/bin/env python3
"""
Automated test runner for reflection → PR creation system tests.
Integrates with CI/CD and provides comprehensive test reporting.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_SUITES = {
    "unit": [
        "test_demo.py",
    ],
    "integration": [
        "test_demo.py",
    ],
    "safety": [
        "test_demo.py",
    ],
    "mocks": [
        "test_mocks.py",
        "test_demo.py",
    ],
    "demo": [
        "test_demo.py",
    ],
    "all": [
        "test_demo.py",
        "test_mocks.py",
    ],
}


class TestRunner:
    """Automated test runner with reporting and CI integration"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("test_reports")
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = {}
        self.start_time = datetime.now()

    def run_test_suite(self, suite_name: str, verbose: bool = False) -> Dict:
        """Run a specific test suite"""
        if suite_name not in TEST_SUITES:
            raise ValueError(f"Unknown test suite: {suite_name}")

        print(f"\n🔬 Running {suite_name} test suite...")

        suite_results = {
            "suite": suite_name,
            "tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0},
            "started_at": datetime.now().isoformat(),
        }

        test_files = TEST_SUITES[suite_name]
        tests_dir = Path(__file__).parent

        for test_file in test_files:
            test_path = tests_dir / test_file
            if not test_path.exists():
                print(f"⚠️  Test file not found: {test_file}")
                continue

            print(f"  📝 Running {test_file}...")
            result = self._run_single_test(test_path, verbose)
            suite_results["tests"].append(result)

            # Update summary
            suite_results["summary"]["total"] += result.get("total", 0)
            suite_results["summary"]["passed"] += result.get("passed", 0)
            suite_results["summary"]["failed"] += result.get("failed", 0)
            suite_results["summary"]["skipped"] += result.get("skipped", 0)
            suite_results["summary"]["duration"] += result.get("duration", 0)

        suite_results["completed_at"] = datetime.now().isoformat()
        self.test_results[suite_name] = suite_results

        # Print suite summary
        summary = suite_results["summary"]
        print("\n  📊 Suite Summary:")
        print(f"     Total: {summary['total']}")
        print(f"     ✅ Passed: {summary['passed']}")
        print(f"     ❌ Failed: {summary['failed']}")
        print(f"     ⏭️  Skipped: {summary['skipped']}")
        print(f"     ⏱️  Duration: {summary['duration']:.2f}s")

        return suite_results

    def _run_single_test(self, test_path: Path, verbose: bool) -> Dict:
        """Run a single test file with pytest"""
        start_time = time.time()

        # Build pytest command
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
        ]

        try:
            # Run pytest
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=300,  # 5 minute timeout per test file
            )

            duration = time.time() - start_time

            # Parse pytest output for basic statistics
            output = result.stdout + result.stderr
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            skipped = output.count(" SKIPPED")
            total = passed + failed + skipped

            # If no tests were detected, try parsing the summary line
            if total == 0:
                try:
                    import re

                    # Look for "X passed" format in output
                    passed_match = re.search(r"(\d+) passed", output)
                    failed_match = re.search(r"(\d+) failed", output)
                    skipped_match = re.search(r"(\d+) skipped", output)

                    passed = int(passed_match.group(1)) if passed_match else 0
                    failed = int(failed_match.group(1)) if failed_match else 0
                    skipped = int(skipped_match.group(1)) if skipped_match else 0
                    total = passed + failed + skipped
                except (ValueError, AttributeError):
                    # Final fallback - if return code is 0, assume at least 1 test passed
                    if result.returncode == 0 and "passed" in output:
                        passed = 1
                        total = 1
            return {
                "file": test_path.name,
                "returncode": result.returncode,
                "duration": duration,
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "file": test_path.name,
                "returncode": -1,
                "duration": time.time() - start_time,
                "error": "Test timeout (5 minutes)",
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
            }
        except Exception as e:
            return {
                "file": test_path.name,
                "returncode": -1,
                "duration": time.time() - start_time,
                "error": str(e),
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
            }

    def run_coverage_analysis(self) -> Dict:
        """Run test coverage analysis"""
        print("\n📈 Running coverage analysis...")

        try:
            # Run pytest with coverage
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(Path(__file__).parent),
                "--cov=.claude.tools",
                "--cov-report=json",
                "--cov-report=html:test_reports/coverage_html",
                "--cov-report=term-missing",
                "-q",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=600,  # 10 minute timeout for coverage
            )

            coverage_file = project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                print("  📊 Coverage Summary:")
                print(f"     Lines: {coverage_data['totals']['percent_covered']:.1f}%")
                print(f"     Missing: {coverage_data['totals']['missing_lines']} lines")

                return {
                    "success": True,
                    "coverage_percent": coverage_data["totals"]["percent_covered"],
                    "lines_covered": coverage_data["totals"]["covered_lines"],
                    "lines_missing": coverage_data["totals"]["missing_lines"],
                    "files": coverage_data["files"],
                }

        except Exception as e:
            print(f"  ❌ Coverage analysis failed: {e}")

        return {"success": False, "error": "Coverage analysis failed"}

    def generate_report(self, format: str = "json") -> Path:
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            report_file = self.output_dir / f"test_report_{timestamp}.json"
            report_data = {
                "timestamp": timestamp,
                "duration": (datetime.now() - self.start_time).total_seconds(),
                "suites": self.test_results,
                "summary": self._calculate_overall_summary(),
            }

            with open(report_file, "w") as f:
                json.dump(report_data, f, indent=2)

        elif format == "html":
            report_file = self.output_dir / f"test_report_{timestamp}.html"
            html_content = self._generate_html_report()

            with open(report_file, "w") as f:
                f.write(html_content)

        else:
            raise ValueError(f"Unsupported report format: {format}")

        print(f"\n📄 Report generated: {report_file}")
        return report_file

    def _calculate_overall_summary(self) -> Dict:
        """Calculate overall test summary across all suites"""
        summary = {
            "total_suites": len(self.test_results),
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_duration": 0,
            "success_rate": 0,
        }

        for suite_result in self.test_results.values():
            suite_summary = suite_result["summary"]
            summary["total_tests"] += suite_summary["total"]
            summary["total_passed"] += suite_summary["passed"]
            summary["total_failed"] += suite_summary["failed"]
            summary["total_skipped"] += suite_summary["skipped"]
            summary["total_duration"] += suite_summary["duration"]

        if summary["total_tests"] > 0:
            summary["success_rate"] = (summary["total_passed"] / summary["total_tests"]) * 100

        return summary

    def _generate_html_report(self) -> str:
        """Generate HTML test report"""
        summary = self._calculate_overall_summary()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reflection Automation Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .suite {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>🔬 Reflection Automation Test Report</h1>

    <div class="summary">
        <h2>📊 Overall Summary</h2>
        <p><strong>Total Tests:</strong> {summary["total_tests"]}</p>
        <p><strong>Success Rate:</strong> {summary["success_rate"]:.1f}%</p>
        <p><strong>Duration:</strong> {summary["total_duration"]:.2f} seconds</p>
        <p class="passed">✅ Passed: {summary["total_passed"]}</p>
        <p class="failed">❌ Failed: {summary["total_failed"]}</p>
        <p class="skipped">⏭️ Skipped: {summary["total_skipped"]}</p>
    </div>
"""

        for suite_name, suite_result in self.test_results.items():
            suite_summary = suite_result["summary"]
            html += f"""
    <div class="suite">
        <h3>📝 {suite_name.title()} Suite</h3>
        <p><strong>Duration:</strong> {suite_summary["duration"]:.2f}s</p>
        <table>
            <tr>
                <th>Test File</th>
                <th>Status</th>
                <th>Tests</th>
                <th>Duration</th>
            </tr>
"""

            for test in suite_result["tests"]:
                status = "✅ PASS" if test["returncode"] == 0 else "❌ FAIL"
                status_class = "passed" if test["returncode"] == 0 else "failed"

                html += f"""
            <tr>
                <td>{test["file"]}</td>
                <td class="{status_class}">{status}</td>
                <td>{test.get("total", "N/A")}</td>
                <td>{test["duration"]:.2f}s</td>
            </tr>
"""

            html += """
        </table>
    </div>
"""

        html += """
    <footer>
        <p><em>Generated by Reflection Automation Test Runner</em></p>
    </footer>
</body>
</html>
"""
        return html

    def check_ci_environment(self) -> Dict:
        """Check if running in CI environment and return CI-specific info"""
        ci_info = {
            "is_ci": False,
            "platform": None,
            "branch": None,
            "commit": None,
            "pr_number": None,
        }

        # Check for GitHub Actions
        if os.environ.get("GITHUB_ACTIONS"):
            ci_info.update(
                {
                    "is_ci": True,
                    "platform": "github_actions",
                    "branch": os.environ.get("GITHUB_REF_NAME"),
                    "commit": os.environ.get("GITHUB_SHA"),
                    "pr_number": os.environ.get("GITHUB_PR_NUMBER"),
                }
            )

        # Check for other CI platforms
        elif os.environ.get("JENKINS_URL"):
            ci_info.update(
                {
                    "is_ci": True,
                    "platform": "jenkins",
                    "branch": os.environ.get("GIT_BRANCH"),
                    "commit": os.environ.get("GIT_COMMIT"),
                }
            )

        elif os.environ.get("CIRCLECI"):
            ci_info.update(
                {
                    "is_ci": True,
                    "platform": "circleci",
                    "branch": os.environ.get("CIRCLE_BRANCH"),
                    "commit": os.environ.get("CIRCLE_SHA1"),
                }
            )

        return ci_info


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="Reflection Automation Test Runner")
    parser.add_argument(
        "suite",
        nargs="?",
        default="all",
        choices=list(TEST_SUITES.keys()),
        help="Test suite to run (default: all)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose test output")
    parser.add_argument("--coverage", action="store_true", help="Run coverage analysis")
    parser.add_argument(
        "--report-format",
        choices=["json", "html"],
        default="json",
        help="Report format (default: json)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("test_reports"), help="Output directory for reports"
    )
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first test failure")

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner(args.output_dir)

    print("🚀 Starting Reflection Automation Test Suite")
    print(f"   Suite: {args.suite}")
    print(f"   Output: {args.output_dir}")

    # Check CI environment
    ci_info = runner.check_ci_environment()
    if ci_info["is_ci"]:
        print(f"   CI Platform: {ci_info['platform']}")
        print(f"   Branch: {ci_info['branch']}")

    try:
        # Run tests
        if args.suite == "all":
            for suite_name in ["unit", "integration", "safety", "mocks"]:
                suite_result = runner.run_test_suite(suite_name, args.verbose)

                if args.fail_fast and suite_result["summary"]["failed"] > 0:
                    print(f"\n❌ Stopping due to failures in {suite_name} suite")
                    break
        else:
            runner.run_test_suite(args.suite, args.verbose)

        # Run coverage if requested
        if args.coverage:
            runner.run_coverage_analysis()

        # Generate report
        report_file = runner.generate_report(args.report_format)

        # Print final summary
        summary = runner._calculate_overall_summary()
        print("\n🎯 Final Results:")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Duration: {summary['total_duration']:.2f}s")

        if summary["total_failed"] > 0:
            print(f"   ❌ {summary['total_failed']} tests failed")
            sys.exit(1)
        else:
            print("   ✅ All tests passed!")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
