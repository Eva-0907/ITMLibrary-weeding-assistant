.PHONY: help setup dev-venv run clean

# Ignore system pip config to avoid extra indexes (e.g., GitLab)
export PIP_CONFIG_FILE := /dev/null

# Detect OS (works on Windows with Make, macOS, Linux)
ifeq ($(OS),Windows_NT)
    PYTHON := python
    PYTHON_BIN := Scripts
    RM := del /Q
    RMDIR := rmdir /S /Q
else
    PYTHON := python3
    PYTHON_BIN := bin
    RM := rm -f
    RMDIR := rm -rf
endif

help:
	@echo "ITM Library Weeding Assistant - Available Commands"
	@echo ""
	@echo "  make dev-venv   Set up development environment (virtual env + dependencies)"
	@echo "  make setup      Complete setup (alias for dev-venv + message)"
	@echo "  make run        Run the weeding agent (requires setup first)"
	@echo "  make clean      Remove build artifacts and cache files"
	@echo ""

setup: dev-venv
	@echo "✓ Setup complete!"
	@echo ""
	@echo "To run the weeding agent:"
	@echo "  make run"
	@echo ""

dev-venv:
	@echo "Setting up development environment..."
ifeq ($(OS),Windows_NT)
	@if not exist .venv ( \
		echo Creating virtual environment... && \
		$(PYTHON) -m venv .venv && \
		.venv\Scripts\pip install --index-url https://pypi.org/simple/ --upgrade pip setuptools wheel \
	)
	.venv\Scripts\pip install --index-url https://pypi.org/simple/ openpyxl requests beautifulsoup4 urllib3 sparp
else
	@if [ ! -d .venv ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv .venv; \
		.venv/$(PYTHON_BIN)/pip install --index-url https://pypi.org/simple/ --upgrade pip setuptools wheel; \
	fi
	.venv/$(PYTHON_BIN)/pip install --index-url https://pypi.org/simple/ openpyxl requests beautifulsoup4 urllib3 sparp
endif
	@echo "✓ Development environment ready"

install: dev-venv
	@echo "✓ Dependencies installed"

run:
ifeq ($(OS),Windows_NT)
	@if not exist .venv ( \
		echo Error: Virtual environment not found. Please run: make setup && \
		exit 1 \
	)
	set PYTHONPATH=./src && .venv\Scripts\python -m itm_weeding.main input/books_1950-1990_book_infile.txt --students "input/Uitleen_collega's.csv" --staff input/Uitleen_2019-2026.csv $(ARGS)
else
	@if [ ! -d .venv ]; then \
		echo "Error: Virtual environment not found. Please run: make setup"; \
		exit 1; \
	fi
	PYTHONPATH=./src .venv/$(PYTHON_BIN)/python -m itm_weeding.main input/books_1950-1990_book_infile.txt --students "input/Uitleen_collega's.csv" --staff input/Uitleen_2019-2026.csv $(ARGS)
endif

run-concurrent:
	$(MAKE) run ARGS="--concurrent"

clean:
	@echo "Cleaning up..."
ifeq ($(OS),Windows_NT)
	@if exist build ( $(RMDIR) build )
	@if exist dist ( $(RMDIR) dist )
	@if exist "*.egg-info" ( del /S /Q *.egg-info )
	@if exist .pytest_cache ( $(RMDIR) .pytest_cache )
	@if exist .coverage ( del .coverage )
	@for /d /r . %d in (__pycache__) do @if exist "%d" $(RMDIR) "%d"
else
	$(RMDIR) build dist *.egg-info .pytest_cache .coverage 2>/dev/null || true
	find . -type d -name __pycache__ -exec $(RMDIR) {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
endif
	@echo "✓ Cleaned"
