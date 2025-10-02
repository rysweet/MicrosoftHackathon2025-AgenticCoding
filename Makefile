# Makefile for Scenarios Directory Pattern Tools
# Provides easy access to production-ready scenario tools

.PHONY: help analyze-codebase scenarios-help list-scenarios

# Default target - show help
help:
	@echo "Scenarios Directory Pattern - Production Tools"
	@echo "============================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make analyze-codebase TARGET=<path> [OPTIONS=<opts>]  - Analyze codebase structure and patterns"
	@echo "  make list-scenarios                                   - List all available scenario tools"
	@echo "  make scenarios-help                                   - Show detailed help for scenarios"
	@echo ""
	@echo "Examples:"
	@echo "  make analyze-codebase TARGET=./src"
	@echo "  make analyze-codebase TARGET=./src OPTIONS='--format json --depth deep'"
	@echo ""

# List all available scenario tools
list-scenarios:
	@echo "Available Scenario Tools:"
	@echo "========================"
	@for dir in .claude/scenarios/*/; do \
		if [ -f "$$dir/tool.py" ]; then \
			tool_name=$$(basename "$$dir"); \
			description=$$(grep -o "^# .*" "$$dir/README.md" | head -1 | sed 's/^# //'); \
			echo "  $$tool_name: $$description"; \
		fi \
	done
	@echo ""
	@echo "Use 'make <tool-name>' to run a specific tool"

# Show detailed help for scenarios system
scenarios-help:
	@echo "Scenarios Directory Pattern Help"
	@echo "==============================="
	@echo ""
	@echo "The scenarios directory contains production-ready tools that follow"
	@echo "amplihack's ruthless simplicity philosophy. Each tool is:"
	@echo ""
	@echo "- Self-contained and fully functional"
	@echo "- Thoroughly tested and documented"
	@echo "- Integrated with amplihack agents and workflow"
	@echo "- Secure and validates all inputs"
	@echo ""
	@echo "Tool Structure:"
	@echo "  .claude/scenarios/<tool-name>/"
	@echo "  ├── README.md                 # Tool documentation"
	@echo "  ├── HOW_TO_CREATE_YOUR_OWN.md # Creation guide"
	@echo "  ├── tool.py                   # Main implementation"
	@echo "  ├── tests/                    # Test suite"
	@echo "  └── examples/                 # Usage examples"
	@echo ""
	@echo "For more information, see: .claude/scenarios/README.md"

# Scenario Tools
# =============

# Analyze Codebase Tool
analyze-codebase:
	@echo "🔍 Running Codebase Analysis..."
	@if [ -z "$(TARGET)" ]; then \
		echo "Error: TARGET is required"; \
		echo "Usage: make analyze-codebase TARGET=<path> [OPTIONS=<opts>]"; \
		echo "Example: make analyze-codebase TARGET=./src"; \
		exit 1; \
	fi
	@python .claude/scenarios/analyze-codebase/tool.py $(TARGET) $(OPTIONS)

# Template for adding new scenario tools:
# Replace {tool-name} with actual tool name
#
# {tool-name}:
# 	@echo "🚀 Running {Tool Name}..."
# 	@if [ -z "$(TARGET)" ]; then \
# 		echo "Error: TARGET is required"; \
# 		echo "Usage: make {tool-name} TARGET=<path> [OPTIONS=<opts>]"; \
# 		exit 1; \
# 	fi
# 	@python .claude/scenarios/{tool-name}/tool.py $(TARGET) $(OPTIONS)

# Development targets for scenarios
dev-scenarios:
	@echo "Development commands for scenarios:"
	@echo "  make test-scenarios    - Run all scenario tests"
	@echo "  make lint-scenarios    - Lint all scenario code"
	@echo "  make new-scenario      - Create new scenario template"

# Run tests for all scenarios
test-scenarios:
	@echo "🧪 Running scenario tests..."
	@for dir in .claude/scenarios/*/; do \
		if [ -d "$$dir/tests" ]; then \
			echo "Testing $$(basename $$dir)..."; \
			cd "$$dir" && python -m pytest tests/ -v; \
		fi \
	done

# Lint all scenario code
lint-scenarios:
	@echo "🔍 Linting scenario code..."
	@find .claude/scenarios -name "*.py" -exec python -m flake8 {} \;

# Create new scenario from template
new-scenario:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required"; \
		echo "Usage: make new-scenario NAME=<tool-name>"; \
		echo "Example: make new-scenario NAME=generate-docs"; \
		exit 1; \
	fi
	@echo "📝 Creating new scenario: $(NAME)"
	@mkdir -p .claude/ai_working/$(NAME)
	@cp .claude/scenarios/templates/README_TEMPLATE.md .claude/ai_working/$(NAME)/README.md
	@cp .claude/scenarios/templates/HOW_TO_CREATE_YOUR_OWN_TEMPLATE.md .claude/ai_working/$(NAME)/HOW_TO_CREATE_YOUR_OWN.md
	@touch .claude/ai_working/$(NAME)/prototype.py
	@touch .claude/ai_working/$(NAME)/notes.md
	@mkdir -p .claude/ai_working/$(NAME)/examples
	@echo "✅ Scenario template created in .claude/ai_working/$(NAME)/"
	@echo "   Start developing your tool there, then graduate to scenarios/"
