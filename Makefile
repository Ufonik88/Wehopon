.PHONY: help dev install reinstall test lint type clean run ui

PYTHON ?= python3
VENV   ?= .venv
ACT    = . $(VENV)/bin/activate

help:  ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(ACT) && pip install --upgrade pip

dev: $(VENV)/bin/activate  ## Create venv and install handshakelab in editable mode (+ dev deps).
	$(ACT) && pip install -e ".[dev]"
	@echo
	@echo "✓ Installed. Activate with:  source $(VENV)/bin/activate"
	@echo "  Run 'handshakelab doctor' to verify."

install: $(VENV)/bin/activate  ## Create venv and install handshakelab (no dev deps).
	$(ACT) && pip install -e .

reinstall:  ## Force-reinstall the editable install (recovery for O3).
	$(ACT) && pip install -e ".[dev]" --force-reinstall
	@echo "✓ Reinstalled. Try: handshakelab --version"

test:  ## Run pytest with coverage.
	$(ACT) && pytest

lint:  ## Run ruff lint.
	$(ACT) && ruff check src/ tests/

type:  ## Run mypy strict.
	$(ACT) && mypy src/handshakelab/

clean:  ## Remove venv, caches, and build artifacts.
	rm -rf $(VENV) build dist src/*.egg-info src/handshakelab.egg-info .pytest_cache .ruff_cache .mypy_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

run:  ## Launch the web UI (requires sudo for capture).
	$(ACT) && sudo -E handshakelab ui

ui: run  ## Alias for 'run'.
