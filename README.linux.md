# Linux / macOS setup

This project requires Python 3.13.x.

## 1. Create the environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

## 2. Install uv and dependencies

```bash
python -m pip install --upgrade pip
python -m pip install uv
uv sync --python 3.13
```

## 3. Run the project

```bash
make run
```

To run the concurrent mode:

```bash
make run-concurrent
```

To skip the UniCat cache and re-fetch all data:

```bash
make run NO_CACHE=1
```

## 4. Useful commands

```bash
make setup
make run
make run NO_CACHE=1
make run-concurrent
make clean
```

Use the Makefile on Linux/macOS. On Windows, use the batch launcher instead: .\run.bat setup
