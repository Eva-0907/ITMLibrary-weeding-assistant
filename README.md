# ITM Library Weeding Assistant

A collection of scripts and helpers to support evidence-based weeding (deaccession) and "keep" decisions for ITM Library collections.

**Intent:** provide a reproducible, data-driven workflow that combines circulation data, catalogue lookups, and local knowledge to recommend items for retention, relocation, or removal.

**Audience:** librarians, collection managers, and support staff who will run the pipeline and interpret the outputs.

## Contents of this README
- **Overview:** goals and guiding principles for weeding decisions
- **Decision framework:** detailed criteria and thresholds used to decide "keep" vs "weed"
- **Inputs & data:** explanation of `input/` files and how they map to criteria
- **How to run:** commands, typical workflow, and validation steps
- **Repository layout:** concise map to scripts and helpers
- **Examples:** sample decision rules and interpretation of outputs
- **Contributing & contact**

## Overview — goals and guiding principles

- Preserve core research and teaching collections essential to ITM's mission.
- Prioritise items with demonstrable usage, curricular relevance, unique holdings, or intrinsic/historical value.
- Remove duplicates, heavily worn copies, or low-use material that is readily available electronically or via shared collections.
- Make decisions transparent and reproducible: record inputs, rules, and outputs for auditing.

Weed decisions should not be taken solely by automated scores. The scripts provide recommendations; a human curator should review flagged items and contextual metadata before final action.

## Decision framework — criteria and recommended thresholds

Use a weighted rule set combining quantitative signals (circulation counts, last-loan date, number of local copies) and qualitative signals (condition, curriculum relevance, local demand).

Common criteria (examples):

- **Circulation (Total loans):** low use suggests candidate for removal. Example threshold: fewer than 2 loans in last 10 years -> candidate.
- **Recent activity (Years since last loan):** items not loaned in >5–10 years reduce retention score.
- **Duplication:** multiple local copies or holdings present in shared collections (consortia) -> consider removing extras.
- **Format & availability:** items available online or via vendor subscription are lower priority to keep physical copies.
- **Subject relevance / curriculum alignment:** items central to active courses or strategic collections should be kept despite low loan counts.
- **Edition/Accuracy:** superseded editions of textbooks or manuals may be weeded if newer editions are present.
- **Cultural/historical value:** local history, special collections, or materials with provenance should be retained.

## Inputs & data mapping

Primary inputs live in the `input/` folder and are used by the `weed/` scripts.

- `books_1950-1990_book_infile.txt`: bibliographic inventory extract used for metadata like ISBN, title, author, year in RIS format.
- `Uitleen_2019-2026.csv`: circulation history (loan events) used to calculate total loans and last-loan date.
- `Uitleen_collega's.csv`: colleague loans and special circulation patterns (may be excluded from public-use counts if desired).

Best practices for inputs:
- Ensure date columns parse correctly and CSV uses UTF-8.
- Trim and normalise identifiers (ISBN, local barcode) so they match catalogue lookups.

## How the scripts use the data

- `unicat/` scripts perform catalogue lookups to augment records (holdings counts, location, edition). Use these to detect duplicates and external availability.
- `weed/` scripts compute metrics (total loans, years-since-last-loan, local-holding-count), apply scoring rules, and emit candidate lists.
- `weed/build_final.py` orchestrates the pipeline, combining inputs and producing the final recommendation CSV.

Run the pipeline from the repository root. Example:

```powershell
python weed/build_final.py
```

Or run components individually for debugging:

```powershell
python unicat/unicat_lookup3.py --help
python weed/weed9.py --help
```

## Output and interpretation

Typical outputs (CSV or Excel) include:

- `weeding_report.xlsx` — full report of all of the records with a reasoning, result of UniCat lookup and category ("KEEP", "WEED", "REVIEW", "SKIP")
- `audit_log.csv` — record of input files, parameters, and timestamp for reproducibility


## Validation and auditing

- Store copies of input files and parameter settings for each run in an `archive/` folder.
- Keep `audit_log.csv` with who ran the process, when, and the parameter values used.

## Repository layout

- `input/` — input data files used by the scripts
  - `books_1950-1990_book_infile.txt`
  - `Uitleen_2019-2026.csv`
  - `Uitleen_collega's.csv`
- `resources/` — supporting materials and notes
- `unicat/` — lookup helpers for the local Unicat system
- `weed/` — main weeding scripts and pipeline


## Contributing

If you'd like to improve scoring, add new criteria, or integrate external APIs, please open an issue describing the change and include example input and expected output. Pull requests should include tests or example runs.

## Contact

Open an issue in the repository for questions or reach out to the project owner.

