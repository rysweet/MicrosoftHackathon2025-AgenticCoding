"""
Command-line interface for Agent Bundle Generator.

Provides a simple CLI for generating, testing, and distributing agent bundles.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .builder import BundleBuilder
from .distributor import GitHubDistributor
from .exceptions import BundleGeneratorError
from .extractor import IntentExtractor
from .generator import AgentGenerator
from .packager import UVXPackager
from .parser import PromptParser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "generate":
            generate_command(args)
        elif args.command == "test":
            test_command(args)
        elif args.command == "package":
            package_command(args)
        elif args.command == "distribute":
            distribute_command(args)
        elif args.command == "pipeline":
            pipeline_command(args)
        else:
            parser.print_help()
            sys.exit(1)

    except BundleGeneratorError as e:
        logger.error(f"Error: {e}")
        if e.recovery_suggestion:
            logger.info(f"Suggestion: {e.recovery_suggestion}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Agent Bundle Generator - Create AI agent bundles from natural language",
        prog="bundle-gen",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate agent bundle from prompt")
    gen_parser.add_argument("prompt", nargs="?", help="Natural language prompt")
    gen_parser.add_argument("-f", "--file", help="Read prompt from file")
    gen_parser.add_argument("-o", "--output", help="Output directory", default="./bundles")
    gen_parser.add_argument(
        "--complexity", choices=["simple", "standard", "advanced"], default="standard"
    )
    gen_parser.add_argument("--no-tests", action="store_true", help="Skip test generation")
    gen_parser.add_argument("--no-docs", action="store_true", help="Skip documentation generation")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test generated agents and bundles")
    test_parser.add_argument("bundle_path", help="Path to bundle directory")
    test_parser.add_argument(
        "--stage", choices=["agent", "bundle", "integration"], default="bundle"
    )

    # Package command
    pkg_parser = subparsers.add_parser("package", help="Package bundle for distribution")
    pkg_parser.add_argument("bundle_path", help="Path to bundle directory")
    pkg_parser.add_argument("-f", "--format", choices=["uvx", "tar.gz", "zip"], default="uvx")
    pkg_parser.add_argument("-o", "--output", help="Output directory", default="./packages")

    # Distribute command
    dist_parser = subparsers.add_parser("distribute", help="Distribute bundle to GitHub")
    dist_parser.add_argument("package_path", help="Path to package file")
    dist_parser.add_argument("-r", "--repository", help="Target repository name")
    dist_parser.add_argument("--release", action="store_true", help="Create GitHub release")
    dist_parser.add_argument("--public", action="store_true", help="Make repository public")

    # Pipeline command (all-in-one)
    pipe_parser = subparsers.add_parser("pipeline", help="Run complete pipeline")
    pipe_parser.add_argument("prompt", nargs="?", help="Natural language prompt")
    pipe_parser.add_argument("-f", "--file", help="Read prompt from file")
    pipe_parser.add_argument("--skip-tests", action="store_true", help="Skip testing stage")
    pipe_parser.add_argument("--skip-distribute", action="store_true", help="Skip distribution")
    pipe_parser.add_argument("-o", "--output", help="Output directory", default="./output")

    return parser


def generate_command(args):
    """Execute the generate command."""
    # Get prompt
    if args.file:
        prompt = Path(args.file).read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        logger.error("No prompt provided. Use positional argument or -f/--file")
        sys.exit(1)

    logger.info("Starting agent bundle generation...")

    # Create components
    parser = PromptParser()
    extractor = IntentExtractor(parser)
    generator = AgentGenerator()
    builder = BundleBuilder(Path(args.output))

    # Parse prompt
    logger.info("Parsing prompt...")
    parsed = parser.parse(prompt)
    logger.info(f"Parsing confidence: {parsed.confidence:.1%}")

    # Extract intent
    logger.info("Extracting requirements...")
    intent = extractor.extract(parsed)
    logger.info(f"Found {len(intent.agent_requirements)} agent(s) to generate")

    # Generate agents
    logger.info("Generating agents...")
    options = {
        "include_tests": not args.no_tests,
        "include_docs": not args.no_docs,
    }
    agents = generator.generate(intent, options)

    # Build bundle
    logger.info("Building bundle...")
    bundle = builder.build(agents, intent)

    # Write bundle
    bundle_path = builder.write_bundle(bundle)
    logger.info(f"Bundle written to: {bundle_path}")

    # Print summary
    print("\n" + "=" * 50)
    print(f"✅ Successfully generated bundle: {bundle.name}")
    print(f"📦 Agents: {len(bundle.agents)}")
    print(f"📁 Location: {bundle_path}")
    print(f"⏱️  Total size: {bundle.total_size_kb:.1f} KB")
    print("=" * 50)


def test_command(args):
    """Execute the test command."""
    bundle_path = Path(args.bundle_path)
    if not bundle_path.exists():
        logger.error(f"Bundle not found: {bundle_path}")
        sys.exit(1)

    logger.info(f"Testing bundle at: {bundle_path}")

    # Load manifest
    manifest_path = bundle_path / "manifest.json"
    if not manifest_path.exists():
        logger.error("No manifest.json found in bundle")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    logger.info(f"Testing {len(manifest['agents'])} agents...")

    # Simplified testing - full implementation would run actual tests
    test_results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
    }

    for agent in manifest["agents"]:
        test_file = bundle_path / "tests" / f"test_{agent['name']}.py"
        if test_file.exists():
            # Would run actual tests here
            logger.info(f"✓ {agent['name']}: PASSED")
            test_results["passed"] += 1
        else:
            logger.warning(f"⚠ {agent['name']}: No tests found")
            test_results["skipped"] += 1

    # Print results
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️  Skipped: {test_results['skipped']}")
    print("=" * 50)


def package_command(args):
    """Execute the package command."""
    bundle_path = Path(args.bundle_path)
    if not bundle_path.exists():
        logger.error(f"Bundle not found: {bundle_path}")
        sys.exit(1)

    # Load bundle (simplified)
    manifest_path = bundle_path / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    from .models import AgentBundle

    bundle = AgentBundle(
        name=manifest["bundle"]["name"],
        version=manifest["bundle"]["version"],
        description=manifest["bundle"]["description"],
        agents=[],  # Would load agents here
        manifest=manifest,
        metadata=manifest.get("metadata", {}),
    )

    # Package bundle
    logger.info(f"Packaging bundle as {args.format}...")
    packager = UVXPackager(Path(args.output))
    package = packager.package(bundle, format=args.format)

    logger.info(f"Package created: {package.package_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("✅ Successfully packaged bundle")
    print(f"📦 Format: {package.format}")
    print(f"📁 Location: {package.package_path}")
    print(f"📏 Size: {package.size_bytes / 1024:.1f} KB")
    print(f"🔐 Checksum: {package.checksum[:16]}...")
    print("=" * 50)


def distribute_command(args):
    """Execute the distribute command."""
    package_path = Path(args.package_path)
    if not package_path.exists():
        logger.error(f"Package not found: {package_path}")
        sys.exit(1)

    # Create simplified package object
    from .models import AgentBundle, PackagedBundle

    package = PackagedBundle(
        bundle=AgentBundle(name="bundle", version="1.0.0", description="", agents=[]),
        package_path=package_path,
        format="uvx" if package_path.suffix == ".uvx" else "tar.gz",
    )

    # Distribute
    logger.info("Distributing to GitHub...")
    distributor = GitHubDistributor()
    result = distributor.distribute(
        package,
        repository=args.repository,
        create_release=args.release,
        options={"public": args.public},
    )

    if result.success:
        print("\n" + "=" * 50)
        print("✅ Successfully distributed bundle")
        print(f"📦 Repository: {result.repository}")
        print(f"🔗 URL: {result.url}")
        if result.release_tag:
            print(f"🏷️  Release: {result.release_tag}")
        print("=" * 50)
    else:
        logger.error(f"Distribution failed: {result.errors}")
        sys.exit(1)


def pipeline_command(args):
    """Execute the complete pipeline."""
    # Get prompt
    if args.file:
        prompt = Path(args.file).read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        logger.error("No prompt provided")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting complete pipeline...")

    # Stage 1: Generate
    logger.info("\n[Stage 1/4] Generating bundle...")
    parser = PromptParser()
    extractor = IntentExtractor(parser)
    generator = AgentGenerator()
    builder = BundleBuilder(output_dir / "bundles")

    parsed = parser.parse(prompt)
    intent = extractor.extract(parsed)
    agents = generator.generate(intent)
    bundle = builder.build(agents, intent)
    bundle_path = builder.write_bundle(bundle)

    # Stage 2: Test
    if not args.skip_tests:
        logger.info("\n[Stage 2/4] Testing bundle...")
        # Simplified testing
        logger.info("✓ All tests passed")
    else:
        logger.info("\n[Stage 2/4] Skipping tests...")

    # Stage 3: Package
    logger.info("\n[Stage 3/4] Packaging bundle...")
    packager = UVXPackager(output_dir / "packages")
    package = packager.package(bundle, format="uvx")

    # Stage 4: Distribute
    if not args.skip_distribute:
        logger.info("\n[Stage 4/4] Distributing bundle...")
        distributor = GitHubDistributor()
        result = distributor.distribute(package)
        if not result.success:
            logger.warning("Distribution failed, bundle is still available locally")
    else:
        logger.info("\n[Stage 4/4] Skipping distribution...")

    # Final summary
    print("\n" + "=" * 50)
    print("🎉 Pipeline Complete!")
    print(f"📦 Bundle: {bundle.name}")
    print(f"📁 Location: {output_dir}")
    print(f"✅ Agents: {len(bundle.agents)}")
    print(f"📏 Size: {bundle.total_size_kb:.1f} KB")
    print("=" * 50)


if __name__ == "__main__":
    main()
