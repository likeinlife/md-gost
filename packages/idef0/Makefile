# Run these targets from packages/idef0; uv installs dependencies into .venv.
UV := uv
RUN := $(UV) run --group dev

.PHONY: help gallery test lint types check

help:
	@printf '%s\n' \
	  'make gallery  — regenerate all gallery PNGs in e2e/img/' \
	  'make test     — run unit, model-combination and end-to-end tests' \
	  'make lint     — run Ruff and wemake-python-styleguide' \
	  'make types    — run Pyrefly in strict mode' \
	  'make check    — run all checks above (without regenerating the gallery)'

gallery:
	$(RUN) python -m e2e.gallery

test:
	$(RUN) pytest

lint:
	$(RUN) ruff check .
	$(RUN) ruff format --check .
	$(RUN) flake8 --config setup.cfg idef0 e2e tests

types:
	$(RUN) pyrefly check

check: lint types test
