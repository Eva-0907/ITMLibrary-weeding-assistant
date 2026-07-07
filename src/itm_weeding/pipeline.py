"""UniCat lookup, record processing and post-processing passes."""

import sys
from datetime import datetime

from itm_weeding.core import apply_rules, get_year, get_isbn, get_authors, gf


class WeedingPipeline:
    """Runs UniCat lookup, applies weeding rules and post-processes results."""

    def __init__(self, unicat, unicat_cache, no_cache=False):
        self.unicat = unicat
        self.unicat_cache = unicat_cache
        self.no_cache = no_cache

    def fetch_unicat_data(self, process_records):
        """Fetch and cache UniCat data for all ISBNs in the records to process."""
        all_isbns = [get_isbn(rec) for rec in process_records]
        unique_isbns = {isbn for isbn in all_isbns if isbn}

        isbns_to_fetch = {
            isbn
            for isbn in unique_isbns
            if self.no_cache or not self.unicat_cache.get(isbn)
        }

        if not isbns_to_fetch:
            print("Pre-fetching UniCat data...")
            print("  All ISBNs already cached")
            return

        print(f"Pre-fetching UniCat data for {len(isbns_to_fetch):,} ISBNs...")
        # The lookup client (concurrent or sequential) decides the strategy.
        batch_results = self.unicat.batch_check_isbns(
            list(isbns_to_fetch),
            show_progress=True,
        )

        fetched = sum(1 for v in batch_results.values() if v is not None)
        print(f"  Fetched {fetched:,} results — storing in cache")
        for isbn, result in batch_results.items():
            self.unicat_cache.set(isbn, result)

    def process_records(
        self,
        process_records,
        records,
        borrowed,
        indexer,
    ):
        """Apply weeding rules to every record. Returns (output_rows, counts)."""
        t0 = datetime.now()
        output_rows = []
        counts = {"KEEP": 0, "WEED": 0, "REVIEW": 0, "SKIP": 0}

        for i, rec in enumerate(process_records):
            result = apply_rules(
                rec,
                records,
                borrowed,
                indexer.isbn_counts,
                older_edition=(i in indexer.older_edition_indices),
                translation_duplicate=(i in indexer.translation_weed_indices),
                barnard_counts=indexer.barnard_counts,
            )
            rec_val = result["recommendation"]
            counts[rec_val] = counts.get(rec_val, 0) + 1

            isbn = get_isbn(rec)

            # Always read from cache (populated during fetch_unicat_data)
            unicat_result = None
            if isbn:
                cached = self.unicat_cache.get(isbn)
                if cached:
                    unicat_result = cached.get("result")

            output_rows.append(
                {
                    "row_index": i,
                    "rec": rec,
                    "result": result,
                    "title": gf(rec, "T1", "TI") or "Untitled",
                    "author": get_authors(rec),
                    "year": get_year(rec) or "",
                    "rec_type": gf(rec, "TY").upper(),
                    "isbn": isbn,
                    "location": gf(rec, "U2").strip(),
                    "unicat_result": unicat_result,
                }
            )

            if (i + 1) % 100 == 0 or (i + 1) == len(records):
                elapsed = (datetime.now() - t0).total_seconds()
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                total = len(records)
                done = i + 1
                bar_width = 30
                filled = int(bar_width * done / total)
                bar = "█" * filled + "░" * (bar_width - filled)
                pct = done / total * 100
                suffix = (
                    f"K={counts['KEEP']} W={counts['WEED']} "
                    f"R={counts['REVIEW']} S={counts['SKIP']} "
                    f"({rate:.0f}/s)"
                )
                end = "\n" if done == total else ""
                sys.stdout.write(
                    f"\r  [{bar}] {pct:5.1f}%  {suffix}  "
                )
                if end:
                    sys.stdout.write("\n")
                sys.stdout.flush()

        self._report_unicat_stats(output_rows)
        return output_rows, counts

    @staticmethod
    def _report_unicat_stats(output_rows):
        """Print UniCat holdings statistics."""
        unicat_held = sum(
            1 for row in output_rows if row.get("unicat_result") == "held"
        )
        unicat_checked = sum(
            1 for row in output_rows if row.get("unicat_result") is not None
        )
        if unicat_checked:
            print(
                f"  UniCat: {unicat_held:,} items held in Belgian libraries "
                f"({unicat_checked:,} checked)"
            )

    @staticmethod
    def upgrade_volume_sets(output_rows, volume_set_indices):
        """Upgrade WEED volumes to KEEP when another volume in the set is kept."""
        kept_volume_groups = set()
        for row in output_rows:
            i = row["row_index"]
            if row["result"]["recommendation"] == "KEEP" and i in volume_set_indices:
                kept_volume_groups.add(volume_set_indices[i])

        if not kept_volume_groups:
            return

        upgraded = 0
        for row in output_rows:
            i = row["row_index"]
            if (
                row["result"]["recommendation"] == "WEED"
                and i in volume_set_indices
                and volume_set_indices[i] in kept_volume_groups
            ):
                row["result"]["recommendation"] = "KEEP"
                row["result"]["reasoning"] += (
                    " | Kept: part of multi-volume set where another volume is kept."
                )
                row["result"]["flags"].append(
                    {
                        "criterion": "Volume set",
                        "detail": "Part of multi-volume set — another volume is kept",
                        "severity": "keep",
                    }
                )
                upgraded += 1
        if upgraded:
            print(f"  Volume sets: {upgraded} volumes upgraded from WEED to KEEP")

    @staticmethod
    def report_translation_duplicates(output_rows):
        """Print a summary of flagged non-English translation duplicates."""
        trans_weeded = sum(
            1
            for row in output_rows
            if any(f["criterion"] == "Translation" for f in row["result"]["flags"])
        )
        if trans_weeded:
            print(f"  Translations: {trans_weeded} non-English duplicates flagged")

    @staticmethod
    def print_summary(counts, process_count, elapsed):
        """Print final processing statistics."""
        rate = process_count / elapsed if elapsed > 0 else 0
        print(f"\nDone in {elapsed:.1f}s  ({rate:.0f} records/sec)")
        print(f"  KEEP:   {counts['KEEP']:>6,}")
        print(f"  WEED:   {counts['WEED']:>6,}")
        print(f"  REVIEW: {counts['REVIEW']:>6,}")
        print(f"  SKIP:   {counts['SKIP']:>6,}")
