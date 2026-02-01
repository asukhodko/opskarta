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
VENV_DIR := venv

# Python - prefer venv if it exists
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

ifeq ($(wildcard $(VENV_PYTHON)),)
  # No venv, try system Python
  PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
  PIP := $(PYTHON) -m pip
else
  # Use venv Python
  PYTHON := $(VENV_PYTHON)
  PIP := $(VENV_PIP)
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
# Virtual Environment
# ============================================================================

.PHONY: venv
venv: $(VENV_DIR)/bin/activate ## Create virtual environment

$(VENV_DIR)/bin/activate:
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	python3 -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "$(YELLOW)Run 'source $(VENV_DIR)/bin/activate' to activate$(NC)"

.PHONY: venv-clean
venv-clean: ## Remove virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)Done!$(NC)"

# ============================================================================
# Dependencies
# ============================================================================

.PHONY: deps
deps: venv ## Install Python dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install pyyaml jsonschema
	@echo "$(GREEN)Dependencies installed!$(NC)"

.PHONY: deps-dev
deps-dev: deps ## Install development dependencies (testing, linting)
	@echo "$(GREEN)Installing dev dependencies...$(NC)"
	$(PIP) install pytest pytest-cov ruff
	@echo "$(GREEN)Dev dependencies installed!$(NC)"

.PHONY: deps-all
deps-all: deps-dev ## Install all dependencies (alias for deps-dev)

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

.PHONY: build-spec-min
build-spec-min: ## Build minified SPEC.min.md using codex
	@echo "$(GREEN)Building SPEC.min.md...$(NC)"
	codex --ask-for-approval never \
		-c hide_agent_reasoning=true \
		-c model_reasoning_effort='"low"' \
		-c model_reasoning_summary='"none"' \
		-c model_verbosity='"low"' \
		exec --sandbox read-only --color never \
		-o $(SPEC_DIR)/SPEC.min.md \
		- < $(TOOLS_DIR)/prompts/spec_minify.prompt.txt
	@echo "$(GREEN)Done!$(NC)"

# ============================================================================
# Validation
# ============================================================================

.PHONY: validate
validate: validate-examples ## Validate all YAML files

.PHONY: validate-examples
validate-examples: ## Validate example files
	@echo "$(GREEN)Validating examples...$(NC)"
	@for dir in $(EXAMPLES_DIR)/*/; do \
		plan=$$(ls "$$dir"*.plan.yaml 2>/dev/null | head -1); \
		views=$$(ls "$$dir"*.views.yaml 2>/dev/null | head -1); \
		if [ -n "$$plan" ]; then \
			echo "  Validating: $$plan"; \
			if [ -n "$$views" ]; then \
				$(PYTHON) $(TOOLS_DIR)/validate.py "$$plan" "$$views" || exit 1; \
			else \
				$(PYTHON) $(TOOLS_DIR)/validate.py "$$plan" || exit 1; \
			fi; \
		fi; \
	done
	@echo "$(GREEN)All examples valid!$(NC)"

.PHONY: validate-schema
validate-schema: ## Validate JSON schemas are valid JSON
	@echo "$(GREEN)Validating JSON schemas...$(NC)"
	@for schema in $(SCHEMAS_DIR)/*.schema.json; do \
		echo "  Checking: $$schema"; \
		$(PYTHON) -c "import json; json.load(open('$$schema'))" || exit 1; \
	done
	@echo "$(GREEN)All schemas valid JSON!$(NC)"

.PHONY: validate-hello
validate-hello: ## Validate hello example (quick check)
	@echo "$(GREEN)Validating hello example...$(NC)"
	$(PYTHON) $(TOOLS_DIR)/validate.py \
		$(EXAMPLES_DIR)/hello/hello.plan.yaml \
		$(EXAMPLES_DIR)/hello/hello.views.yaml
	@echo "$(GREEN)Valid!$(NC)"

.PHONY: validate-program
validate-program: ## Validate program example
	@echo "$(GREEN)Validating program example...$(NC)"
	$(PYTHON) $(TOOLS_DIR)/validate.py \
		$(EXAMPLES_DIR)/program/program.plan.yaml \
		$(EXAMPLES_DIR)/program/program.views.yaml
	@echo "$(GREEN)Valid!$(NC)"

# ============================================================================
# Rendering
# ============================================================================

.PHONY: render-hello
render-hello: ## Render hello example Gantt diagram
	@echo "$(GREEN)Rendering hello example...$(NC)"
	cd $(SPEC_DIR) && $(CURDIR)/$(PYTHON) -m tools.render.plan2gantt \
		--plan examples/hello/hello.plan.yaml \
		--views examples/hello/hello.views.yaml \
		--view overview

.PHONY: render-program
render-program: ## Render program example (list views)
	@echo "$(GREEN)Rendering program example views...$(NC)"
	cd $(SPEC_DIR) && $(CURDIR)/$(PYTHON) -m tools.render.plan2gantt \
		--plan examples/program/program.plan.yaml \
		--views examples/program/program.views.yaml \
		--list-views

# ============================================================================
# Testing
# ============================================================================

.PHONY: test
test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	@if $(PYTHON) -c "import pytest" 2>/dev/null; then \
		$(PYTHON) -m pytest $(TESTS_DIR) -v --tb=short; \
	else \
		echo "$(YELLOW)pytest not installed, running basic tests...$(NC)"; \
		$(PYTHON) $(TESTS_DIR)/test_scheduling.py; \
	fi
	@echo "$(GREEN)Tests complete!$(NC)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTHON) $(TESTS_DIR)/test_scheduling.py

.PHONY: test-coverage
test-coverage: deps-dev ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TESTS_DIR) -v --cov=$(TOOLS_DIR) --cov-report=term-missing

# ============================================================================
# Linting and Formatting
# ============================================================================

.PHONY: lint
lint: ## Lint Python code (requires ruff)
	@echo "$(GREEN)Linting Python code...$(NC)"
	@if $(PYTHON) -c "import ruff" 2>/dev/null; then \
		$(PYTHON) -m ruff check $(TOOLS_DIR); \
	else \
		echo "$(YELLOW)ruff not installed, run 'make deps-dev' first$(NC)"; \
	fi

.PHONY: format
format: ## Format Python code (requires ruff)
	@echo "$(GREEN)Formatting Python code...$(NC)"
	@if $(PYTHON) -c "import ruff" 2>/dev/null; then \
		$(PYTHON) -m ruff format $(TOOLS_DIR); \
	else \
		echo "$(YELLOW)ruff not installed, run 'make deps-dev' first$(NC)"; \
	fi

# ============================================================================
# CI targets
# ============================================================================

.PHONY: ci
ci: deps check-spec validate test ## Run all CI checks
	@echo "$(GREEN)All CI checks passed!$(NC)"

.PHONY: check
check: validate-schema validate build-spec ## Quick check (schemas, examples, spec)
	@echo "$(GREEN)All checks passed!$(NC)"

# ============================================================================
# Quick Start
# ============================================================================

.PHONY: quickstart
quickstart: venv deps validate-hello render-hello ## Quick start: setup venv, install deps, validate and render hello
	@echo ""
	@echo "$(GREEN)Quick start complete!$(NC)"
	@echo "Try running:"
	@echo "  make validate-examples"
	@echo "  make test"

# ============================================================================
# Clean
# ============================================================================

.PHONY: clean
clean: ## Clean generated files (keeps venv)
	@echo "$(YELLOW)Cleaning...$(NC)"
	rm -rf $(EXAMPLES_DIR)/output
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "$(GREEN)Clean!$(NC)"

.PHONY: clean-all
clean-all: clean venv-clean ## Clean everything including venv
	@echo "$(GREEN)All clean!$(NC)"
