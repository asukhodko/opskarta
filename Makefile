# opskarta Makefile
# Build, validate, and test opskarta specifications

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ============================================================================
# Configuration
# ============================================================================

VENV_DIR := venv
VENV_PYTHON := $(VENV_DIR)/bin/python

ifeq ($(wildcard $(VENV_PYTHON)),)
  PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
else
  PYTHON := $(VENV_PYTHON)
endif

# Colors
G := \033[0;32m
Y := \033[0;33m
N := \033[0m

# ============================================================================
# Help
# ============================================================================

.PHONY: help
help: ## Show this help
	@echo "opskarta - Development Tools"
	@echo ""
	@echo "Quick start:  make quickstart"
	@echo "Run CI:       make ci        (v1 only)"
	@echo "              make ci-v2     (v2 only)"
	@echo "              make ci-all    (both)"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(G)%-18s$(N) %s\n", $$1, $$2}'

# ============================================================================
# Setup
# ============================================================================

.PHONY: venv deps deps-dev quickstart

venv: $(VENV_DIR)/bin/activate ## Create virtual environment

$(VENV_DIR)/bin/activate:
	@echo "$(G)Creating venv...$(N)"
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip -q
	@echo "$(Y)Run: source $(VENV_DIR)/bin/activate$(N)"

deps: venv ## Install dependencies
	@$(VENV_DIR)/bin/pip install pyyaml jsonschema -q
	@echo "$(G)Dependencies installed$(N)"

deps-dev: deps ## Install dev dependencies
	@$(VENV_DIR)/bin/pip install pytest pytest-cov ruff -q
	@echo "$(G)Dev dependencies installed$(N)"

quickstart: deps ## Quick start: setup and validate
	@$(PYTHON) specs/v1/tools/validate.py \
		specs/v1/en/examples/hello/hello.plan.yaml \
		specs/v1/en/examples/hello/hello.views.yaml
	@echo "$(G)Ready! Try: make test$(N)"

# ============================================================================
# v1 Specification
# ============================================================================

.PHONY: spec-v1 check-spec-v1 validate-v1 test-v1 ci-v1

spec-v1: ## Build v1 SPEC.md (en + ru)
	@$(PYTHON) specs/v1/tools/build_spec.py --lang en
	@$(PYTHON) specs/v1/tools/build_spec.py --lang ru
	@echo "$(G)v1 SPEC.md built$(N)"

check-spec-v1: ## Check v1 SPEC.md is up-to-date
	@$(PYTHON) specs/v1/tools/build_spec.py --lang en --check
	@$(PYTHON) specs/v1/tools/build_spec.py --lang ru --check

validate-v1: ## Validate v1 examples and schemas
	@echo "$(G)Validating v1...$(N)"
	@for schema in specs/v1/schemas/*.schema.json; do \
		$(PYTHON) -c "import json; json.load(open('$$schema'))" || exit 1; \
	done
	@for dir in specs/v1/en/examples/*/; do \
		plan=$$(ls "$$dir"*.plan.yaml 2>/dev/null | head -1); \
		views=$$(ls "$$dir"*.views.yaml 2>/dev/null | head -1); \
		[ -n "$$plan" ] && $(PYTHON) specs/v1/tools/validate.py "$$plan" $$views || exit 1; \
	done
	@for dir in specs/v1/ru/examples/*/; do \
		plan=$$(ls "$$dir"*.plan.yaml 2>/dev/null | head -1); \
		views=$$(ls "$$dir"*.views.yaml 2>/dev/null | head -1); \
		[ -n "$$plan" ] && $(PYTHON) specs/v1/tools/validate.py "$$plan" $$views || exit 1; \
	done
	@echo "$(G)v1 valid$(N)"

test-v1: ## Run v1 tests
	@$(PYTHON) -m pytest specs/v1/tests/ -v --tb=short

ci-v1: deps check-spec-v1 validate-v1 test-v1 ## Run v1 CI checks
	@echo "$(G)v1 CI passed$(N)"

# Aliases for backward compatibility
.PHONY: spec-en spec-ru test ci
spec-en: ; @$(PYTHON) specs/v1/tools/build_spec.py --lang en
spec-ru: ; @$(PYTHON) specs/v1/tools/build_spec.py --lang ru
test: test-v1
ci: ci-v1

# ============================================================================
# v2 Specification
# ============================================================================

.PHONY: spec-v2 check-spec-v2 validate-v2 test-v2 ci-v2

spec-v2: ## Build v2 SPEC.md (en + ru)
	@$(PYTHON) specs/v2/tools/build_spec.py --lang en
	@$(PYTHON) specs/v2/tools/build_spec.py --lang ru
	@echo "$(G)v2 SPEC.md built$(N)"

check-spec-v2: ## Check v2 SPEC.md is up-to-date
	@$(PYTHON) specs/v2/tools/build_spec.py --lang en --check
	@$(PYTHON) specs/v2/tools/build_spec.py --lang ru --check

validate-v2: ## Validate v2 examples and schemas
	@echo "$(G)Validating v2...$(N)"
	@for schema in specs/v2/schemas/*.schema.json; do \
		$(PYTHON) -c "import json; json.load(open('$$schema'))" || exit 1; \
	done
	@cd specs/v2 && for dir in en/examples/*/; do \
		$(CURDIR)/$(PYTHON) -m tools.cli validate "$$dir"*.plan.yaml || exit 1; \
	done
	@cd specs/v2 && for dir in ru/examples/*/; do \
		$(CURDIR)/$(PYTHON) -m tools.cli validate "$$dir"*.plan.yaml || exit 1; \
	done
	@echo "$(G)v2 valid$(N)"

test-v2: ## Run v2 tests
	@PYTHONPATH=$(CURDIR) $(PYTHON) -m pytest specs/v2/tests/ -v --tb=short

ci-v2: check-spec-v2 validate-v2 test-v2 ## Run v2 CI checks
	@echo "$(G)v2 CI passed$(N)"

# ============================================================================
# Combined targets
# ============================================================================

.PHONY: spec-all test-all ci-all clean

spec-all: spec-v1 spec-v2 ## Build all SPEC.md files

test-all: test-v1 test-v2 ## Run all tests

ci-all: ci-v1 ci-v2 ## Run all CI checks
	@echo "$(G)All CI passed$(N)"

clean: ## Clean generated files
	@rm -rf __pycache__ .pytest_cache .coverage htmlcov
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "$(G)Clean$(N)"

clean-all: clean ## Clean everything including venv
	@rm -rf $(VENV_DIR)
	@echo "$(G)All clean$(N)"
