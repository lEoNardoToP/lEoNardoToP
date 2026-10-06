PYTHON ?= python3

.PHONY: install test lint serve demo baseline shift

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

serve:
	atlasguard serve

baseline:
	atlasguard demo --count 120

shift:
	atlasguard demo --shifted --count 120

demo: baseline shift
