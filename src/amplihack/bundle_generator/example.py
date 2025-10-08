"""
Example usage of the Agent Bundle Generator.

This script demonstrates the complete workflow from prompt to distributed bundle.
"""

from pathlib import Path

from .builder import BundleBuilder
from .distributor import GitHubDistributor
from .extractor import IntentExtractor
from .generator import AgentGenerator
from .packager import UVXPackager
from .parser import PromptParser


def example_simple_generation():
    """Example: Generate a simple agent bundle."""
    print("=" * 60)  # noqa: T201 (print)
    print("Example 1: Simple Agent Generation")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)

    # Natural language prompt
    prompt = """
    Create a data validation agent that checks JSON schemas and
    reports errors with detailed feedback. It should validate
    structure, data types, and required fields.
    """

    # Initialize components
    parser = PromptParser()
    extractor = IntentExtractor(parser)
    generator = AgentGenerator()
    builder = BundleBuilder()

    # Parse and extract
    parsed = parser.parse(prompt)
    print(f"\n✓ Parsed prompt (confidence: {parsed.confidence:.1%})")  # noqa: T201 (print)
    print(f"  - Sentences: {len(parsed.sentences)}")  # noqa: T201 (print)
    print(f"  - Key phrases: {parsed.key_phrases[:3]}")  # noqa: T201 (print)

    intent = extractor.extract(parsed)
    print("\n✓ Extracted intent")  # noqa: T201 (print)
    print(f"  - Action: {intent.action}")  # noqa: T201 (print)
    print(f"  - Domain: {intent.domain}")  # noqa: T201 (print)
    print(f"  - Complexity: {intent.complexity}")  # noqa: T201 (print)
    print(f"  - Agents: {len(intent.agent_requirements)}")  # noqa: T201 (print)

    # Generate agents
    agents = generator.generate(intent)
    print(f"\n✓ Generated {len(agents)} agent(s)")  # noqa: T201 (print)
    for agent in agents:
        print(f"  - {agent.name}: {agent.role} ({agent.file_size_kb:.1f} KB)")  # noqa: T201 (print)

    # Build bundle
    bundle = builder.build(agents, intent, name="json_validator_bundle")
    print(f"\n✓ Built bundle: {bundle.name}")  # noqa: T201 (print)
    print(f"  - Version: {bundle.version}")  # noqa: T201 (print)
    print(f"  - Total size: {bundle.total_size_kb:.1f} KB")  # noqa: T201 (print)

    # Write to disk
    bundle_path = builder.write_bundle(bundle)
    print(f"\n✓ Bundle written to: {bundle_path}")  # noqa: T201 (print)

    return bundle


def example_multi_agent_bundle():
    """Example: Generate a multi-agent bundle."""
    print("\n" + "=" * 60)  # noqa: T201 (print)
    print("Example 2: Multi-Agent Bundle Generation")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)

    prompt = """
    Create a comprehensive security analysis suite with the following agents:

    1. Vulnerability Scanner Agent - Scans code for security vulnerabilities
    2. Dependency Audit Agent - Checks dependencies for known CVEs
    3. Configuration Validator Agent - Validates security configurations
    4. Report Generator Agent - Creates detailed security reports

    All agents should work together to provide complete security coverage.
    """

    # Initialize components
    parser = PromptParser()
    extractor = IntentExtractor(parser)
    generator = AgentGenerator()
    builder = BundleBuilder()
    packager = UVXPackager()

    # Generate bundle
    parsed = parser.parse(prompt)
    intent = extractor.extract(parsed)

    print(f"\n✓ Detected {len(intent.agent_requirements)} agents to generate:")  # noqa: T201 (print)
    for req in intent.agent_requirements:
        print(f"  - {req.name}: {req.purpose}")  # noqa: T201 (print)

    agents = generator.generate(intent, {"include_tests": True, "include_docs": True})
    bundle = builder.build(agents, intent, name="security_suite")

    print(f"\n✓ Generated bundle with {len(bundle.agents)} agents")  # noqa: T201 (print)

    # Package for distribution
    package = packager.package(bundle, format="uvx")
    print("\n✓ Packaged bundle:")  # noqa: T201 (print)
    print(f"  - Format: {package.format}")  # noqa: T201 (print)
    print(f"  - Size: {package.size_bytes / 1024:.1f} KB")  # noqa: T201 (print)
    print(f"  - Path: {package.package_path}")  # noqa: T201 (print)

    return package


def example_complete_pipeline():
    """Example: Complete pipeline from prompt to distribution."""
    print("\n" + "=" * 60)  # noqa: T201 (print)
    print("Example 3: Complete Pipeline")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)

    prompt = """
    Create a performance monitoring agent that tracks application metrics,
    identifies bottlenecks, and provides optimization suggestions.
    It should monitor CPU, memory, and I/O operations.
    """

    try:
        # Initialize all components
        parser = PromptParser()
        extractor = IntentExtractor(parser)
        generator = AgentGenerator()
        builder = BundleBuilder()
        packager = UVXPackager()
        GitHubDistributor()

        # Stage 1: Parse and Extract
        print("\n[Stage 1] Parsing and extracting requirements...")  # noqa: T201 (print)
        parsed = parser.parse(prompt)
        intent = extractor.extract(parsed)
        print(f"✓ Extracted {intent.action} request in {intent.domain} domain")  # noqa: T201 (print)

        # Stage 2: Generate Agents
        print("\n[Stage 2] Generating agents...")  # noqa: T201 (print)
        agents = generator.generate(intent)
        print(f"✓ Generated {len(agents)} agent(s)")  # noqa: T201 (print)

        # Stage 3: Build Bundle
        print("\n[Stage 3] Building bundle...")  # noqa: T201 (print)
        bundle = builder.build(agents, intent)
        bundle_path = builder.write_bundle(bundle)
        print(f"✓ Bundle written to: {bundle_path}")  # noqa: T201 (print)

        # Stage 4: Test (simplified)
        print("\n[Stage 4] Testing bundle...")  # noqa: T201 (print)
        issues = builder.validate_bundle(bundle)
        if issues:
            print(f"⚠ Validation issues: {issues}")  # noqa: T201 (print)
        else:
            print("✓ Bundle validation passed")  # noqa: T201 (print)

        # Stage 5: Package
        print("\n[Stage 5] Packaging for distribution...")  # noqa: T201 (print)
        package = packager.package(bundle, format="uvx")
        print(f"✓ Created {package.format} package: {package.package_path}")  # noqa: T201 (print)

        # Stage 6: Distribute (optional)
        print("\n[Stage 6] Distribution (simulated)...")  # noqa: T201 (print)
        print("✓ Ready for distribution to GitHub/PyPI")  # noqa: T201 (print)
        # Actual distribution would require credentials:
        # result = distributor.distribute(package, repository="my-agent-bundle")

        print("\n" + "=" * 60)  # noqa: T201 (print)
        print("🎉 Pipeline Complete!")  # noqa: T201 (print)
        print(f"Bundle: {bundle.name}")  # noqa: T201 (print)
        print(f"Agents: {len(bundle.agents)}")  # noqa: T201 (print)
        print(f"Package: {package.package_path}")  # noqa: T201 (print)
        print("=" * 60)  # noqa: T201 (print)

        return bundle, package

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")  # noqa: T201 (print)
        return None, None


def example_test_existing_bundle():
    """Example: Test an existing bundle."""
    print("\n" + "=" * 60)  # noqa: T201 (print)
    print("Example 4: Testing Existing Bundle")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)

    # Assume we have a bundle at this path
    bundle_path = Path("./bundles/json_validator_bundle")

    if not bundle_path.exists():
        print("⚠ No existing bundle found. Run example_simple_generation() first.")  # noqa: T201 (print)
        return

    # Load and validate bundle
    builder = BundleBuilder()

    # Load manifest
    import json

    manifest_path = bundle_path / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"✓ Loaded bundle: {manifest['bundle']['name']}")  # noqa: T201 (print)
    print(f"  Agents: {len(manifest['agents'])}")  # noqa: T201 (print)

    # Validate structure
    from .models import AgentBundle

    bundle = AgentBundle(
        name=manifest["bundle"]["name"],
        version=manifest["bundle"]["version"],
        description=manifest["bundle"]["description"],
        agents=[],  # Would load actual agents here
        manifest=manifest,
    )

    issues = builder.validate_bundle(bundle)
    if issues:
        print("\n⚠ Validation issues found:")  # noqa: T201 (print)
        for issue in issues:
            print(f"  - {issue}")  # noqa: T201 (print)
    else:
        print("\n✅ Bundle validation passed!")  # noqa: T201 (print)


def main():
    """Run all examples."""
    print("Agent Bundle Generator - Examples")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)

    # Example 1: Simple generation
    bundle = example_simple_generation()

    # Example 2: Multi-agent bundle
    package = example_multi_agent_bundle()

    # Example 3: Complete pipeline
    bundle, package = example_complete_pipeline()

    # Example 4: Test existing bundle
    example_test_existing_bundle()

    print("\n" + "=" * 60)  # noqa: T201 (print)
    print("All examples completed!")  # noqa: T201 (print)
    print("Check the ./bundles and ./packages directories for output.")  # noqa: T201 (print)
    print("=" * 60)  # noqa: T201 (print)


if __name__ == "__main__":
    main()
