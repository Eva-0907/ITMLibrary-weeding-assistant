# Linux / macOS setup

This project requires Python 3.13.x.

## 1. Create the environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install uv
uv sync --python 3.13
```

## 2. Run the project

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

## 3. Useful commands

```bash
make setup
make run
make run NO_CACHE=1
make run-concurrent
make run-concurrent NO_CACHE=1
```
