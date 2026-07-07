.PHONY: help setup dev-venv install run run-concurrent clean

ifeq ($(OS),Windows_NT)
VENV_PYTHON := .venv\\Scripts\\python.exe
BOOTSTRAP_PYTHON := .uvenv\\Scripts\\python.exe
BOOTSTRAP_UV := .uvenv\\Scripts\\uv.exe
PYTHON_CMD := $(shell where py >nul 2>nul && echo py -3.13 || echo python)
RUN_ARGS := input\\books_1950-1990_book_infile.txt --students input\\Uitleen_collega's.csv --staff input\\Uitleen_2019-2026.csv
else
VENV_PYTHON := .venv/bin/python
BOOTSTRAP_PYTHON := .uvenv/bin/python
BOOTSTRAP_UV := .uvenv/bin/uv
PYTHON_CMD := $(shell python3 --version >/dev/null 2>&1 && echo python3 || echo python)
RUN_ARGS := input/books_1950-1990_book_infile.txt --students input/Uitleen_collega\'s.csv --staff input/Uitleen_2019-2026.csv
endif

# Package index to use. Defaults to the public PyPI; override with:
#   make setup INDEX_URL=https://<user>:<token>@host/pypi/simple/
INDEX_URL ?= https://pypi.org/simple/

help:
	@echo "Usage:"
	@echo "  make setup"
	@echo "  make run"
	@echo "  make run-concurrent"
	@echo "  make clean"

setup: dev-venv

dev-venv:
	@echo "Creating a Python 3.13 virtual environment and installing dependencies..."
	@if [ ! -x "$(BOOTSTRAP_PYTHON)" ]; then \
		$(PYTHON_CMD) -m venv .uvenv; \
	fi
	@PIP_CONFIG_FILE=/dev/null $(BOOTSTRAP_PYTHON) -m pip install --index-url "$(INDEX_URL)" --upgrade pip uv
	@PIP_CONFIG_FILE=/dev/null $(BOOTSTRAP_UV) sync --python 3.13 --index-url "$(INDEX_URL)" --index-strategy first-index

install: dev-venv

NO_CACHE ?=
NO_CACHE_FLAG := $(if $(NO_CACHE),--no-cache,)

run:
	@$(VENV_PYTHON) -m itm_weeding.main $(RUN_ARGS) $(NO_CACHE_FLAG)

run-concurrent:
	@$(VENV_PYTHON) -m itm_weeding.main $(RUN_ARGS) --concurrent $(NO_CACHE_FLAG)

clean:
	@rm -rf build dist .pytest_cache .uvenv
	@find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '.DS_Store' -delete
	@rm -f .coverage
