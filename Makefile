.PHONY: help setup install build update changelog validate status clean test lint format

help:
	@echo "Venice KB Collector - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Install dependencies and Playwright browsers"
	@echo "  install     - Install package in development mode"
	@echo "  build       - Run full knowledge base build"
	@echo "  update      - Incremental update (only fetch changed sources)"
	@echo "  changelog   - Generate changelog from snapshots"
	@echo "  validate    - Validate knowledge base integrity"
	@echo "  status      - Show build status and stats"
	@echo "  test        - Run test suite"
	@echo "  lint        - Run linters (ruff, mypy)"
	@echo "  format      - Format code with black"
	@echo "  clean       - Remove cache and build artifacts"

setup:
	pip install -r requirements-dev.txt
	playwright install chromium

install:
	pip install -e .

build:
	python -m venice_kb build --verbose

update:
	python -m venice_kb update --verbose

changelog:
	python -m venice_kb changelog

validate:
	python -m venice_kb validate

status:
	python -m venice_kb status

test:
	pytest tests/ -v --cov=venice_kb

lint:
	ruff check src/venice_kb tests
	mypy src/venice_kb

format:
	black src/venice_kb tests
	ruff check --fix src/venice_kb tests

clean:
	rm -rf .cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
