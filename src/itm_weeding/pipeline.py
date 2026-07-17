"""UniCat lookup, record processing and post-processing passes."""

import sys
from datetime import datetime

from itm_weeding.core import get_year, get_isbn, get_authors, gf
from itm_weeding.core.rules_engine import RulesEngine


class WeedingPipeline:
    """Applies weeding rules and post-processes results."""

    def __init__(self):
        pass

    def apply_rules(self, rec, all_records, borrowed, isbn_counts,
                    older_edition=False, translation_duplicate=False,
                    barnard_counts=None, unicat_result=None):
        """Apply all weeding decision rules to a single record."""
        engine = RulesEngine(all_records, borrowed, isbn_counts, barnard_counts)
        return engine.get_weed_result(
            rec,
            unicat_result=unicat_result,
            older_edition=older_edition,
            translation_duplicate=translation_duplicate,
        )

    def process_records(self, bib_data, circ_data, unicat_data):
        """Apply weeding rules, run post-processing passes and print summary.

        Returns (output_rows, counts).
        """
        t0 = datetime.now()
        output_rows = []
        counts = {"KEEP": 0, "WEED": 0, "REVIEW": 0, "SKIP": 0}

        indexer = bib_data.indexer
        records = bib_data.records
        borrowed = circ_data.borrowed

        for i, rec in enumerate(bib_data.process_records):
            isbn = get_isbn(rec)

            unicat_result = unicat_data.get(isbn) if isbn else None

            result = self.apply_rules(
                rec,
                records,
                borrowed,
                indexer.isbn_counts,
                older_edition=(i in indexer.older_edition_indices),
                translation_duplicate=(i in indexer.translation_weed_indices),
                barnard_counts=indexer.barnard_counts,
                unicat_result=unicat_result,
            )
            rec_val = result["recommendation"]
            counts[rec_val] = counts.get(rec_val, 0) + 1

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

        # Post-processing passes
        self.upgrade_volume_sets(output_rows, indexer.volume_set_indices)
        self.report_translation_duplicates(output_rows)

        elapsed = (datetime.now() - t0).total_seconds()
        self.print_summary(counts, len(bib_data.process_records), elapsed)

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
