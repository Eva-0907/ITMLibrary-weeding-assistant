# ITM Library Weeding Assistant

A professional weeding decision support system for the ITG Antwerp tropical medicine library collection.

## Overview

The ITM Library Weeding Assistant applies sophisticated decision rules to recommend which books should be:
- **KEEP** — Retain indefinitely
- **WEED** — Remove from collection
- **REVIEW** — Manual review recommended  
- **SKIP** — Not eligible for weeding (e.g., e-only items)

## Key Features

- **Intelligent Rules Engine**: 30+ decision criteria including retention flags, historical significance, outbreak relevance, regional context, and circulation data
- **Barnard Classification Support**: Integrates with medical subject classification to improve decisions
- **UniCat Integration**: Checks Belgian library availability (cached to JSON for efficiency)
- **Multi-Language Handling**: Detects translation duplicates and preserves English editions
- **Volume Set Management**: Groups multi-volume works and preserves complete sets
- **Edition Detection**: Identifies and removes superseded older editions
- **Excel Reports**: Generates detailed two-sheet reports (Library Collection + Department Books)
- **Circulation Tracking**: Incorporates 2019-2026 loan history

## Project Structure

```
itm_weeding_assistant/
├── src/itm_weeding/           # Main package
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   │
│   ├── core/                  # Core weeding logic
│   │   ├── __init__.py
│   │   ├── helpers.py         # Utility functions (get_isbn, get_year, etc.)
│   │   ├── parser.py          # RIS parsing & circulation loading
│   │   └── rules.py           # Main decision engine (apply_rules)
│   │
│   ├── config/                # Configuration & rule data
│   │   ├── __init__.py
│   │   ├── barnard.py         # Medical classification system
│   │   └── rules_data.py      # Historical titles, outbreaks, keywords
│   │
│   ├── unicat/                # UniCat Belgian library lookup
│   │   ├── __init__.py
│   │   ├── cache.py           # JSON caching layer
│   │   └── lookup.py          # Web scraper & availability check
│   │
│   └── report/                # Report generation
│       ├── __init__.py
│       └── builder.py         # Excel export
│
├── data/
│   ├── input/                 # Input files (.ris, .csv)
│   ├── output/                # Generated reports (.xlsx)
│   └── cache/                 # UniCat results cache
│
├── tests/                     # Unit tests
├── Makefile                   # Build automation (cross-platform)
├── pyproject.toml             # Modern Python packaging
├── README.md                  # This file
└── .gitignore
```

## Installation

### Quick Setup (macOS/Linux/Windows)

```bash
make setup
```

This will:
1. Create a Python virtual environment
2. Install dependencies
3. Set up the project in development mode

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install
pip install -e .
```

## Usage

### Run Weeding Agent

```bash
make run
```

Or directly:

```bash
python -m itm_weeding.main data/input/books.ris \
    --students data/input/Uitleen_2019-2026.csv \
    --staff data/input/Uitleen_collega\'s.csv \
    --out data/output/weeding_report.xlsx
```

### Input Files

- **RIS file** (required): Bibliography data in RIS format
- **Student loans CSV** (optional): Semicolon-delimited (Barnard|CallNumber|Year)
- **Staff loans CSV** (optional): Tab-delimited (Barnard|CallNumber|Year)

### Output

- **weeding_report.xlsx**: Two-sheet workbook
  - Sheet 1: Library Collection records
  - Sheet 2: Department Books records

Each record includes:
- Title, Author, Year, ISBN
- Recommendation (KEEP/WEED/REVIEW/SKIP)
- Historical significance flag
- All triggered rules & reasoning
- UniCat check link (for WEED items with ISBN)

## Decision Rules

### Keep Rules (High Priority)

1. **H1 Retention Flag** — Core historical fields (Ethics, History of Medicine, etc.)
2. **Dissertation** — All doctoral dissertations
3. **Historical Titles** — Canonical medical landmark works (30+ titles)
4. **Outbreak Relevance** — Books matching 14 major disease outbreaks
5. **Regional Relevance** — Congo, Belgium, Africa-specific, IRCB/ARSC
6. **Circulation** — Borrowed at least once (2019-2026)
7. **Archives-G** — Curated special collection
8. **Specialist Publishers** — Tropical medicine institutions (15+ publishers)
9. **Conference Proceedings** — Especially tropical medicine focused
10. **Liber Amicorum** — Commemorative editions

### Weed Rules (High Priority)

1. **Translation Duplicates** — Non-English versions when English edition exists
2. **Older Editions** — Superseded by newer edition in collection
3. **Publication Date** — Books published 1950-1990 (retention flag dependent)
   - H3 class: Auto-weed
   - H2 class: Auto-weed (weak)
   - Others: Flag for review
4. **Post-1990 Non-Circulated** — Published after 1990 with no loans

### Review Rules

- WHO/FAO publications (likely open access online)
- No publication year (manual review needed)

### Scarcity Protection

- Barnard classes with ≤2 items kept (unless manual/guideline)
- Multi-volume sets preserved if one volume is kept

## Modern Python Tooling

### Build & Install
- `setuptools` + `wheel` for standard packaging
- `pyproject.toml` (PEP 517/518) replaces setup.py

### Development Tools

```bash
# Run linters
make lint

# Run tests (when available)
make test

# Clean build artifacts
make clean

# Help
make help
```

### Configuration (pyproject.toml)

- **Black**: Code formatting (line-length=100)
- **isort**: Import sorting (Black profile)
- **Flake8**: Linting (max-length=100)
- **pytest**: Testing with coverage
- **mypy**: Type checking (optional)

## UniCat Caching

UniCat lookup results are automatically cached to `data/cache/unicat_cache.json`:

```python
from itm_weeding.unicat import UniCatCache

cache = UniCatCache("data/cache/unicat_cache.json")
result = cache.get("9780123456789")
if result:
    print(f"Cached: {result['result']}")
else:
    # Do new lookup and cache
    status, error = check_unicat_isbn(isbn)
    cache.set(isbn, status)
```

## Module Exports

### Core API

```python
from itm_weeding.core import (
    parse_ris,
    load_circulation,
    apply_rules,
    get_isbn,
    get_year,
    get_authors,
    is_historical_title,
    matches_outbreak,
)

from itm_weeding.unicat import UniCatCache, check_unicat_isbn
from itm_weeding.report import export_xlsx
```

## Configuration Data

All rule data is centralized in `src/itm_weeding/config/`:

- **`barnard.py`**: BARNARD classification (200+ codes) + retention flags
- **`rules_data.py`**: 
  - HISTORICAL_TITLES (70+ landmark works)
  - OUTBREAK_TIMELINE (14 major events)
  - Regional/institutional keywords
  - WHO/FAO/Specialist publisher lists

## Data Structures

### Record Dictionary
RIS format with standard tags (TI, A1, A2, PY, AB, U4, etc.)

### Decision Result
```python
{
    "recommendation": "KEEP|WEED|REVIEW|SKIP",
    "keep_override": bool,
    "hard_rule": str or None,
    "flags": [{"criterion": str, "detail": str, "severity": str}],
    "retention": "H1|H2|H3" or None,
    "historically_significant": bool,
    "historical_reasons": [str],
    "reasoning": str,
}
```

## Requirements

- Python 3.8+
- openpyxl (Excel I/O)
- requests + beautifulsoup4 (UniCat scraping)
- urllib3 (HTTPS)

## License

MIT License — See LICENSE file

## Contact

ITG Antwerp Library
Email: lib@itg.be
Website: https://www.itg.be

---

**Version**: 10.0  
**Last Updated**: 2026-07-02  
**Maintained by**: ITG Antwerp

## Changelog

### v10 (2026-07-02) — Modern Restructure
- Converted to proper Python package (src/ layout)
- Created modular subpackages (core, config, unicat, report)
- Added UniCat caching layer (JSON)
- Implemented modern tooling (pyproject.toml, Black, pytest)
- Added Makefile for cross-platform build automation
- Extracted rule data into centralized config modules
- Added comprehensive type hints and docstrings
- Improved CLI with better error handling

### v9a (Original)
- Multi-volume set handling
- Translation duplicate detection
- Barnard classification gates for outbreaks
- Retention flag-based auto-weeding
