.PHONY: build update changelog test lint format clean setup

setup:
	pip install -e '.[dev]'
	playwright install chromium --with-deps

build:
	python -m venice_kb build --output ./knowledge_base --snapshot-dir ./snapshots

update:
	python -m venice_kb update --output ./knowledge_base --snapshot-dir ./snapshots

changelog:
	python -m venice_kb changelog --snapshot-dir ./snapshots --output ./knowledge_base/CHANGELOG.md

diff:
	python -m venice_kb changelog --snapshot-dir ./snapshots --last-n 2 --severity important

status:
	python -m venice_kb status --kb-path ./knowledge_base --snapshot-dir ./snapshots

test:
	python -m pytest tests/ -v

lint:
	python -m ruff check src/ tests/
	python -m black --check src/ tests/

format:
	python -m black src/ tests/
	python -m ruff check --fix src/ tests/

clean:
	rm -rf .cache/ knowledge_base/ snapshots/ .pytest_cache/
