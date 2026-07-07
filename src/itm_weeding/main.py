#!/usr/bin/env python3
"""
ITM Library Weeding Assistant — Main CLI Entry Point
Tropical Medicine & Global Health collection at ITG Antwerp

Usage:
    python -m itm_weeding.main <ris_file>
    python -m itm_weeding.main <ris_file> --students <csv> --staff <csv> --out <xlsx>
"""

from pathlib import Path
from datetime import datetime

from itm_weeding.cli import CLI
from itm_weeding.loaders import DataLoader
from itm_weeding.grouping import GroupIndexer
from itm_weeding.pipeline import WeedingPipeline
from itm_weeding.report import export_xlsx
from itm_weeding.unicat import (
    UniCatCache,
    UniCatLookupConcurrent,
    UniCatLookupSequential,
)


def main():
    """Main entry point."""
    args = CLI.parse_args()

    # Initialize UniCat cache and lookup client. The lookup strategy is chosen
    # up front: concurrent (SPARP batch) or sequential (one request at a time).
    unicat_cache = UniCatCache()
    if args.concurrent:
        unicat = UniCatLookupConcurrent(concurrency=20)
    else:
        unicat = UniCatLookupSequential()
    if args.no_cache:
        print("UniCat cache DISABLED — all ISBNs will be fetched from API")
    elif len(unicat_cache) > 0:
        print(f"UniCat cache loaded: {len(unicat_cache)} entries")

    # Load input data
    records = DataLoader.load_records(args.ris)
    borrowed = DataLoader.load_borrowed(args.students, args.staff)

    # Pre-compute grouping indices
    indexer = GroupIndexer(records)

    process_records = records
    print(f"\nProcessing {len(process_records):,} records...")

    pipeline = WeedingPipeline(unicat, unicat_cache, no_cache=args.no_cache)

    # Phase 1: collect UniCat data
    pipeline.fetch_unicat_data(process_records)

    # Phase 2: process records
    t0 = datetime.now()
    output_rows, counts = pipeline.process_records(
        process_records, records, borrowed, indexer
    )

    # Post-processing passes
    pipeline.upgrade_volume_sets(output_rows, indexer.volume_set_indices)
    pipeline.report_translation_duplicates(output_rows)

    elapsed = (datetime.now() - t0).total_seconds()
    pipeline.print_summary(counts, len(process_records), elapsed)

    # Export
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting to {args.out}...")
    export_xlsx(output_rows, args.out)
    print(f"Done — {args.out}")


if __name__ == "__main__":
    main()
