.PHONY: help setup dev-venv install run run-concurrent clean

ifeq ($(OS),Windows_NT)
VENV_PYTHON := .venv\\Scripts\\python.exe
PYTHON_CMD := $(shell where py >nul 2>nul && echo py -3.13 || echo python)
RUN_ARGS := input\\books_1950-1990_book_infile.txt --students input\\Uitleen_collega's.csv --staff input\\Uitleen_2019-2026.csv
else
VENV_PYTHON := .venv/bin/python
PYTHON_CMD := $(shell python3 --version 2>/dev/null && echo python3 || echo python)
RUN_ARGS := input/books_1950-1990_book_infile.txt --students input/Uitleen_collega\'s.csv --staff input/Uitleen_2019-2026.csv
endif

help:
	@echo "Usage:"
	@echo "  make setup"
	@echo "  make run"
	@echo "  make run-concurrent"
	@echo "  make clean"

setup: dev-venv

dev-venv:
	@echo "Creating a Python 3.13 virtual environment and installing dependencies..."
	@if [ -x "$(VENV_PYTHON)" ]; then \
		echo "Virtual environment already exists."; \
	else \
		$(PYTHON_CMD) -m venv .venv; \
	fi
	@if [ ! -x "$(VENV_PYTHON)" ]; then \
		echo "Error: virtual environment Python was not created successfully."; \
		exit 1; \
	fi
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PYTHON) -m pip install uv
	@$(VENV_PYTHON) -m uv sync --python 3.13

install: dev-venv

run:
	@$(VENV_PYTHON) -m itm_weeding.main $(RUN_ARGS)

run-concurrent:
	@$(VENV_PYTHON) -m itm_weeding.main $(RUN_ARGS) --concurrent

clean:
	@rm -rf build dist .pytest_cache
	@find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '.DS_Store' -delete
	@rm -f .coverage
