#!/usr/bin/env python3
"""
ITM Library Weeding Assistant — Main CLI Entry Point
Tropical Medicine & Global Health collection at ITG Antwerp

Usage:
    python -m itm_weeding.main <ris_file>
    python -m itm_weeding.main <ris_file> --students <csv> --staff <csv> --out <xlsx>
"""

from pathlib import Path

from itm_weeding.cli import CLI
from itm_weeding.loaders import BibData, UnicatDataLoader, CirculationDataLoader
from itm_weeding.pipeline import WeedingPipeline
from itm_weeding.report import export_xlsx
from itm_weeding.unicat import UniCatCache


def main():
    """Main entry point."""
    args = CLI.parse_args()

    # Phase 1: load data
    unicat_loader = UnicatDataLoader(UniCatCache(), concurrent=args.concurrent, no_cache=args.no_cache)
    bib_data = BibData(args.ris)
    circ_data = CirculationDataLoader.load(args.students, args.staff)
    unicat_data = unicat_loader.load(bib_data.process_records)
    print(f"\nProcessing {len(bib_data.process_records):,} records...")

    # Phase 2: process records (includes post-processing and summary)
    pipeline = WeedingPipeline()
    output_rows, counts = pipeline.process_records(bib_data, circ_data, unicat_data)

    # Export
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting to {args.out}...")
    export_xlsx(output_rows, args.out)
    print(f"Done — {args.out}")


if __name__ == "__main__":
    main()
