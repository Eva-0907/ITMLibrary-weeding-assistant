#!/usr/bin/env python3
"""
Cross-platform task runner for ITM Library Weeding Assistant.
Requires: uv  (https://docs.astral.sh/uv/getting-started/installation/)

Usage:
    python tasks.py help
    python tasks.py setup
    python tasks.py run [extra args]
    python tasks.py run --concurrent
    python tasks.py clean
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VENV = ROOT / ".venv"
BIN = VENV / ("Scripts" if sys.platform == "win32" else "bin")
PYTHON = BIN / ("python.exe" if sys.platform == "win32" else "python")

BOOKS_FILE = "input/books_1950-1990_book_infile.txt"
STUDENTS_FILE = "input/Uitleen_collega's.csv"
STAFF_FILE = "input/Uitleen_2019-2026.csv"


def run(*cmd, env=None, check=True):
    """Run a command, inheriting stdio."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    subprocess.run(list(cmd), env=full_env, check=check, cwd=ROOT)


def cmd_help():
    print(
        """ITM Library Weeding Assistant — Available Commands

  python tasks.py setup          Set up virtual env + install dependencies (uses uv)
  python tasks.py run            Run the weeding agent (requires setup first)
  python tasks.py run-concurrent Run the weeding agent with --concurrent flag
  python tasks.py clean          Remove build artifacts and cache files
"""
    )


def ensure_uv():
    """Install uv if it's not on PATH."""
    if shutil.which("uv"):
        return
    print("uv not found — installing...")
    if sys.platform == "win32":
        run("powershell", "-ExecutionPolicy", "ByPass", "-c",
            "irm https://astral.sh/uv/install.ps1 | iex")
    else:
        run("sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh")
    # The installer adds uv to PATH via shell profile; for the current process
    # we also check the default install location so subsequent calls work.
    local_bin = Path.home() / ".local" / "bin"
    if str(local_bin) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = str(local_bin) + os.pathsep + os.environ.get("PATH", "")
    if not shutil.which("uv"):
        print("Error: uv installation failed. Install manually: https://docs.astral.sh/uv/")
        sys.exit(1)
    print("✓ uv installed")


def cmd_setup():
    ensure_uv()
    print("Creating virtual environment and installing dependencies...")
    run("uv", "sync")
    print("\n✓ Setup complete!")
    print("\nTo run the weeding agent:")
    print("  python tasks.py run")


def cmd_run(extra_args=None):
    if not PYTHON.exists():
        print("Error: virtual environment not found. Please run: python tasks.py setup")
        sys.exit(1)
    args = [
        str(PYTHON), "-m", "itm_weeding.main",
        BOOKS_FILE,
        "--students", STUDENTS_FILE,
        "--staff", STAFF_FILE,
    ]
    if extra_args:
        args.extend(extra_args)
    run(*args, env={"PYTHONPATH": str(ROOT / "src")})


def cmd_clean():
    print("Cleaning up...")
    targets = ["build", "dist", ".pytest_cache"]
    for name in targets:
        p = ROOT / name
        if p.exists():
            shutil.rmtree(p)

    for p in ROOT.rglob("*.egg-info"):
        shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    for p in ROOT.rglob("*.pyc"):
        p.unlink(missing_ok=True)
    for p in ROOT.rglob(".DS_Store"):
        p.unlink(missing_ok=True)
    coverage = ROOT / ".coverage"
    if coverage.exists():
        coverage.unlink()
    print("✓ Cleaned")


COMMANDS = {
    "help": cmd_help,
    "setup": cmd_setup,
    "dev-venv": cmd_setup,
    "install": cmd_setup,
    "run": None,          # handled below
    "run-concurrent": None,
    "clean": cmd_clean,
}

if __name__ == "__main__":
    args = sys.argv[1:]
    command = args[0] if args else "help"

    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        cmd_help()
        sys.exit(1)

    if command == "run":
        extra = args[1:]
        cmd_run(extra if extra else None)
    elif command == "run-concurrent":
        extra = args[1:]
        cmd_run(["--concurrent"] + extra)
    else:
        COMMANDS[command]()
