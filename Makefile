# opskarta Makefile
# Tooling for building, validating, and testing opskarta v1 specification

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Directories
SPEC_DIR := specs/v1
TOOLS_DIR := $(SPEC_DIR)/tools
TESTS_DIR := $(SPEC_DIR)/tests
EXAMPLES_DIR := $(SPEC_DIR)/examples
SCHEMAS_DIR := $(SPEC_DIR)/schemas

# Python detection (local or Docker)
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
DOCKER := $(shell command -v docker 2>/dev/null)

# If no local Python, use Docker
ifndef PYTHON
  ifdef DOCKER
    PYTHON := docker run --rm -v "$(CURDIR):/app" -w /app python:3.11-slim python
    PIP := docker run --rm -v "$(CURDIR):/app" -w /app python:3.11-slim pip
  else
    $(error "No Python or Docker found. Please install Python 3.9+ or Docker.")
  endif
else
  PIP := $(PYTHON) -m pip
endif

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

.PHONY: help
help: ## Show this help message
	@echo "opskarta v1 - Development Tools"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Build
# ============================================================================

.PHONY: build
build: build-spec ## Build all artifacts

.PHONY: build-spec
build-spec: ## Build SPEC.md from spec/ sources
	@echo "$(GREEN)Building SPEC.md...$(NC)"
	$(PYTHON) $(TOOLS_DIR)/build_spec.py
	@echo "$(GREEN)Done!$(NC)"

.PHONY: check-spec
check-spec: ## Check if SPEC.md is up-to-date
	@echo "$(YELLOW)Checking SPEC.md...$(NC)"
	$(PYTHON) $(TOOLS_DIR)/build_spec.py --check

# ============================================================================
# Validation
# ============================================================================

.PHONY: validate
validate: validate-examples validate-fixtures ## Validate all YAML files

.PHONY: validate-examples
validate-examples: ## Validate example files
	@echo "$(GREEN)Validating examples...$(NC)"
	@for dir in $(EXAMPLES_DIR)/*/; do \
		plan=$$(ls "$$dir"*.plan.yaml 2>/dev/null | head -1); \
		views=$$(ls "$$dir"*.views.yaml 2>/dev/null | head -1); \
		if [ -n "$$plan" ]; then \
			echo "  Validating: $$plan"; \
			if [ -n "$$views" ]; then \
				$(PYTHON) $(TOOLS_DIR)/validate.py "$$plan" "$$views" --schema || exit 1; \
			else \
				$(PYTHON) $(TOOLS_DIR)/validate.py "$$plan" --schema || exit 1; \
			fi; \
		fi; \
	done
	@echo "$(GREEN)All examples valid!$(NC)"

.PHONY: validate-fixtures
validate-fixtures: ## Validate test fixtures
	@echo "$(GREEN)Validating fixtures...$(NC)"
	@for plan in $(TESTS_DIR)/fixtures/*.plan.yaml; do \
		if [ -f "$$plan" ]; then \
			echo "  Validating: $$plan"; \
			$(PYTHON) $(TOOLS_DIR)/validate.py "$$plan" --schema || exit 1; \
		fi; \
	done
	@echo "$(GREEN)All fixtures valid!$(NC)"

.PHONY: validate-schema
validate-schema: ## Validate JSON schemas themselves
	@echo "$(GREEN)Validating JSON schemas...$(NC)"
	@for schema in $(SCHEMAS_DIR)/*.schema.json; do \
		echo "  Checking: $$schema"; \
		$(PYTHON) -c "import json; json.load(open('$$schema'))" || exit 1; \
	done
	@echo "$(GREEN)All schemas valid JSON!$(NC)"

# ============================================================================
# Testing
# ============================================================================

.PHONY: test
test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v --tb=short || \
	$(PYTHON) $(TESTS_DIR)/test_scheduling.py
	@echo "$(GREEN)Tests complete!$(NC)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTHON) $(TESTS_DIR)/test_scheduling.py

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v --cov=$(TOOLS_DIR) --cov-report=term-missing

# ============================================================================
# Rendering
# ============================================================================

.PHONY: render-examples
render-examples: ## Render all example Gantt diagrams
	@echo "$(GREEN)Rendering Gantt diagrams...$(NC)"
	@mkdir -p $(EXAMPLES_DIR)/output
	@for dir in $(EXAMPLES_DIR)/*/; do \
		plan=$$(ls "$$dir"*.plan.yaml 2>/dev/null | head -1); \
		views=$$(ls "$$dir"*.views.yaml 2>/dev/null | head -1); \
		if [ -n "$$plan" ] && [ -n "$$views" ]; then \
			name=$$(basename "$$dir"); \
			echo "  Rendering: $$name"; \
			$(PYTHON) -m $(TOOLS_DIR:specs/%=%).render.mermaid_gantt \
				--plan "$$plan" --views "$$views" --list-views 2>/dev/null | \
			grep -E '^\s+-' | sed 's/.*- //' | cut -d: -f1 | while read view; do \
				$(PYTHON) -m $(TOOLS_DIR:specs/%=%).render.mermaid_gantt \
					--plan "$$plan" --views "$$views" --view "$$view" \
					-o "$(EXAMPLES_DIR)/output/$${name}_$${view}.md" 2>/dev/null || true; \
			done; \
		fi; \
	done
	@echo "$(GREEN)Rendering complete!$(NC)"

# ============================================================================
# Development
# ============================================================================

.PHONY: deps
deps: ## Install Python dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install pyyaml jsonschema pytest pytest-cov
	@echo "$(GREEN)Dependencies installed!$(NC)"

.PHONY: lint
lint: ## Lint Python code (requires ruff)
	@echo "$(GREEN)Linting Python code...$(NC)"
	$(PYTHON) -m ruff check $(TOOLS_DIR) $(TESTS_DIR) || \
	echo "$(YELLOW)ruff not installed, skipping lint$(NC)"

.PHONY: format
format: ## Format Python code (requires ruff)
	@echo "$(GREEN)Formatting Python code...$(NC)"
	$(PYTHON) -m ruff format $(TOOLS_DIR) $(TESTS_DIR) || \
	echo "$(YELLOW)ruff not installed, skipping format$(NC)"

# ============================================================================
# Docker helpers
# ============================================================================

.PHONY: docker-test
docker-test: ## Run tests in Docker container
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.11-slim \
		sh -c "pip install -q pyyaml && python $(TESTS_DIR)/test_scheduling.py"

.PHONY: docker-validate
docker-validate: ## Run validation in Docker container
	@echo "$(GREEN)Running validation in Docker...$(NC)"
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.11-slim \
		sh -c "pip install -q pyyaml jsonschema && \
		for plan in $(TESTS_DIR)/fixtures/*.plan.yaml; do \
			echo \"Validating: \$$plan\"; \
			python $(TOOLS_DIR)/validate.py \"\$$plan\" --schema; \
		done"

.PHONY: docker-build
docker-build: ## Build SPEC.md in Docker container
	@echo "$(GREEN)Building SPEC.md in Docker...$(NC)"
	docker run --rm -v "$(CURDIR):/app" -w /app python:3.11-slim \
		python $(TOOLS_DIR)/build_spec.py

.PHONY: docker-shell
docker-shell: ## Open shell in Docker container with Python
	@echo "$(GREEN)Opening Docker shell...$(NC)"
	docker run -it --rm -v "$(CURDIR):/app" -w /app python:3.11-slim bash

# ============================================================================
# CI targets
# ============================================================================

.PHONY: ci
ci: check-spec validate test ## Run all CI checks
	@echo "$(GREEN)All CI checks passed!$(NC)"

.PHONY: ci-docker
ci-docker: docker-build docker-validate docker-test ## Run all CI checks in Docker
	@echo "$(GREEN)All Docker CI checks passed!$(NC)"

# ============================================================================
# Clean
# ============================================================================

.PHONY: clean
clean: ## Clean generated files
	@echo "$(YELLOW)Cleaning...$(NC)"
	rm -rf $(EXAMPLES_DIR)/output
	rm -rf __pycache__ .pytest_cache .coverage
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "$(GREEN)Clean!$(NC)"
